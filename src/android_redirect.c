
#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <dlfcn.h>
#include <dirent.h>
#include <errno.h>
#include <malloc.h>
#include <zlib.h>
#include <sys/mman.h>
#include "android/log.h"

//#define LOG(...) __android_log_print(ANDROID_LOG_INFO, "redirect", __VA_ARGS__)
#define LOG(...)
#define WITH_COMPRESSION 1

typedef struct cookie_io_functions_t {
  ssize_t (*read)(void *cookie, char *buf, size_t n);
  ssize_t (*write)(void *cookie, const char *buf, size_t n);
  int (*seek)(void *cookie, off_t *pos, int whence);
  int (*close)(void *cookie);
} cookie_io_functions_t;

typedef struct fccookie {
  void *cookie;
  FILE *fp;
  ssize_t	(*readfn)(void *, char *, size_t);
  ssize_t	(*writefn)(void *, const char *, size_t);
  int		(*seekfn)(void *, off_t *, int);
  int		(*closefn)(void *);
} fccookie;

static int
fcread(void *cookie, char *buf, int n)
{
  int result;
  fccookie *c = (fccookie *) cookie;
  result = c->readfn (c->cookie, buf, n);
  return result;
}

static int
fcwrite(void *cookie, const char *buf, int n)
{
  int result;
  fccookie *c = (fccookie *) cookie;
  if (c->fp->_flags & __SAPP && c->fp->_seek)
    {
      c->fp->_seek (cookie, 0, SEEK_END);
    }
  result = c->writefn (c->cookie, buf, n);
  return result;
}

static fpos_t
fcseek(void *cookie, fpos_t pos, int whence)
{
  fccookie *c = (fccookie *) cookie;
  off_t offset = (off_t) pos;

  c->seekfn (c->cookie, &offset, whence);

  return (fpos_t) offset;
}

static int
fcclose(void *cookie)
{
  int result = 0;
  fccookie *c = (fccookie *) cookie;
  if (c->closefn)
    {
      result = c->closefn (c->cookie);
    }
  free (c);
  return result;
}

FILE *
fopencookie(void *cookie, const char *mode, cookie_io_functions_t functions)
{
  FILE *fp;
  fccookie *c;
  int flags;
  int dummy;

  if ((flags = __sflags (mode, &dummy)) == 0)
    return NULL;
  if (((flags & (__SRD | __SRW)) && !functions.read)
      || ((flags & (__SWR | __SRW)) && !functions.write))
    {
      return NULL;
    }
  if ((fp = (FILE *) __sfp ()) == NULL)
    return NULL;
  if ((c = (fccookie *) malloc (sizeof *c)) == NULL)
    {
      fp->_flags = 0;
      return NULL;
    }

  fp->_file = -1;
  fp->_flags = flags;
  c->cookie = cookie;
  c->fp = fp;
  fp->_cookie = c;
  c->readfn = functions.read;
  fp->_read = fcread;
  c->writefn = functions.write;
  fp->_write = fcwrite;
  c->seekfn = functions.seek;
  fp->_seek = functions.seek ? fcseek : NULL;
  c->closefn = functions.close;
  fp->_close = fcclose;

  return fp;
}

typedef struct filemap_entry_s {
	const char *source;
	const char *dest;
	int is_dir;
	int is_lib;
	unsigned int len;
	unsigned int off;
	unsigned int zlen;
	struct filemap_entry_s *next;
} filemap_entry_t;

typedef struct filemap_fd_s {
	filemap_entry_t *entry;
	off_t off;
	short index;
	FILE *fp;
#ifdef WITH_COMPRESSION
	char *data;
#endif
} filemap_fd_t;

static filemap_entry_t *entries = NULL;
static int basedirlen = 0;
static char basedir[PATH_MAX];
static char libdir[PATH_MAX];
static FILE *fd_data;
static long fd_data_off = 0;
static long fd_data_len = 0;
static void *fd_data_map = NULL;
static cookie_io_functions_t cookie_funcs;

#define MAX_FFD 1024
#define FFD(x) -2 - x
#define IS_FFD(x) ((x) <= -2)
static filemap_fd_t *fds[MAX_FFD];
static short fd_index = 0;

static FILE * cookie_open(filemap_entry_t *entry, const char *mode) {
	FILE *ret = NULL;
	filemap_fd_t *fd = malloc(sizeof(filemap_fd_t));
	fd->entry = entry;
	fd->off = 0;
	fd->index = 0;
#ifdef WITH_COMPRESSION
	fd->data = NULL;
#endif
	fd->fp = NULL;

	ret = fopencookie((void *)fd, mode, cookie_funcs);
	if (ret == NULL) {
		free(fd);
	} else {
		fd->index = fd_index;
		fd->fp = ret;
		ret->_file = FFD(fd_index);
		fds[fd->index] = fd;
		LOG("~~ cookie_open(%s) fileno=%d", entry->source, fd_index);
		fd_index = (fd_index + 1) % MAX_FFD;
	}
	return ret;
}

static ssize_t cookie_read(void *cookie, char *buf, size_t size) {
	filemap_fd_t *fd = (filemap_fd_t *)cookie;
	ssize_t xbytes;
	if (fd == NULL)
		return -1;

	LOG("~~ cookie_read(fileno=%d size=%d fd->off=%d fd->entry->len=%d)",
			fd->index, size, fd->off, fd->entry->len);

#ifdef WITH_COMPRESSION
	if ( fd->data == NULL ) {
		// mmap ?
		LOG("~~ cookie_read data not uncompress yet, do it now. fd_data_map=%p eoff=%d zlen=%d",
				fd_data_map, fd->entry->off, fd->entry->zlen);
		char *mdest = malloc(sizeof(char) * fd->entry->len);
		if ( mdest == NULL ) {
			LOG("~~ cookie_read error nomem");
			errno = ENOMEM;
			goto end;
		}

		unsigned long destlen = fd->entry->len;
		if ( uncompress(mdest, &destlen, fd_data_map + fd->entry->off, fd->entry->zlen) == -1 ) {
			LOG("~~ cookie_read uncompress() failed");
			goto end;
		}


		LOG("~~ cookie_read uncompress finished -> %d", destlen);
		fd->data = mdest;
		goto ok;

end:;
		if ( mdest ) free(mdest);
		return -1;
ok:;
	}
#endif


	xbytes = size;
	if ( fd->off + size > fd->entry->len )
		xbytes = fd->entry->len - fd->off;
	if ( xbytes < 0 )
		xbytes = 0;

	LOG("~~ cookie_read want to read %d bytes", xbytes);
	memcpy(buf, fd_data_map + fd->entry->off + fd->off, xbytes);
	fd->off += xbytes;
	return xbytes;
}

static ssize_t cookie_write(void *cookie, const char *buf, size_t size) {
	// not supported
	return -1;
}

static int cookie_seek(void *cookie, off_t *offset, int whence) {
	filemap_fd_t *fd = (filemap_fd_t *)cookie;
	if (fd == NULL)
		return -1;

	LOG("~~ cookie_seek(fileno=%d whence=%d offset=%ld)", fd->index, whence, *offset);
	switch ( whence ) {
		case SEEK_SET:
			fd->off = *offset;
			break;

		case SEEK_CUR:
			fd->off += *offset;
			break;

		case SEEK_END:
			fd->off = fd->entry->len + *offset;
			break;

		default:
			return -1;
	}

	*offset = fd->off;
	return 0;
}

static int cookie_close(void *cookie) {
	filemap_fd_t *fd = (filemap_fd_t *)cookie;
	if (fd == NULL)
		return -1;
	LOG("~~ cookie_close(fileno=%d)", fd->index);
	fds[fd->index] = NULL;
#ifdef WITH_COMPRESSION
	if ( fd->data )
		free(fd->data);
#endif
	free(fd);
	return 0;
}

static filemap_entry_t *filemap_entry_add(char *source) {
	filemap_entry_t *entry = (filemap_entry_t *)malloc(sizeof(filemap_entry_t));
	if ( entry == NULL ) {
		return NULL;
	}
	entry->source = strdup(source);
	entry->len = 0;
	entry->zlen = 0;
	entry->is_dir = 0;
	entry->is_lib = 0;
	entry->off = 0;
	entry->next = entries;
	entries = entry;
	return entry;
}


static filemap_entry_t *filemap_entry_find(const char *source) {
	filemap_entry_t *entry = entries;
	while ( entry != NULL ) {
		//LOG("    --> strcmp(%s, %s) = %d", entry->source, source, strcmp(entry->source, source));
		if ( strcmp(entry->source, source) == 0 )
			return entry;
		entry = entry->next;
	}
	return NULL;
}

static filemap_entry_t *find_dir(const char *source) {
	if (strncmp(source, basedir, basedirlen) == 0) {
		return filemap_entry_find(source + basedirlen + 1);
	}
	return filemap_entry_find(source);
}

static int file_exists(const char* fn) {
   return access(fn, F_OK) != -1;
}

static filemap_entry_t *find_file(const char *fn) {
	filemap_entry_t *res = NULL;
	if ( file_exists(fn) ) {
		LOG("  --> really exist on the disk, return the real filename.");
		return NULL;
	}

	if (strncmp(fn, basedir, basedirlen) == 0) {
		LOG("  --> search in the filemap(basedir): %s", fn + basedirlen + 1);
		res = filemap_entry_find(fn + basedirlen + 1);
		LOG("  --> filemap returned %p", res);
		return res;
	}

	if ( fn[0] == '.' && fn[1] == '/' ) {
		LOG("  --> search in the filemap(.): %s", fn + 2);
		res = filemap_entry_find(fn + 2);
		LOG("  --> filemap returned %p", res);
		return res;
	}

	LOG("  --> search in the filemap(no basedir): %s", fn);
	res = filemap_entry_find(fn);
	LOG("  --> filemap returned %p", res);
	return res;
}

static ssize_t getline(char **lineptr, size_t *n, FILE *stream)
{
    char *ptr;
    ptr = fgetln(stream, n);
    if (ptr == NULL)
        return -1;
    if (*lineptr != NULL)
		free(*lineptr);
    size_t len = n[0] + 1;
    n[0] = len;
    *lineptr = malloc(len);
    memcpy(*lineptr, ptr, len-1);
    (*lineptr)[len-1] = '\0';
    return len;
}

static void __android_init(const char *files_directory, const char *libs_directory) {
	char *line = NULL;
	size_t len = 0, off = 0, zlen;
	char *sep, *p;
	char destfn[PATH_MAX];
	char source[PATH_MAX];
	char dest[PATH_MAX];
	int count = 0;
	filemap_entry_t *entry;

	LOG("-- android low-level redirection started --");

	cookie_funcs.read = cookie_read;
	cookie_funcs.write = cookie_write;
	cookie_funcs.seek = cookie_seek;
	cookie_funcs.close = cookie_close;

	snprintf(destfn, PATH_MAX, "%s/libfilemap.so", libs_directory);
	memcpy(basedir, files_directory, strlen(files_directory) + 1);
	memcpy(libdir, libs_directory, strlen(libs_directory) + 1);
	basedirlen = strlen(basedir);

	// load the libfilemap.so
	FILE *f = fopen(destfn, "r");
	if (f == NULL) {
		LOG("-- unable to read %s --", destfn);
		return;
	}

	LOG("-- reading %s --", destfn);
	char *c = NULL;
	while (getline(&line, &len, f) != -1) {
		LOG(" read line");
		line[strlen(line) - 1] = '\0';
		c = line;
		line += 1;
		switch ( *c ) {
			case 'd':
				// directory
				LOG("-- add directory %s --", line);
				entry = filemap_entry_add(line);
				entry->is_dir = 1;
				break;

			case 'l':
				// library
				LOG("-- add library %s --", line);
				strncpy(source, strsep(&line, ";"), PATH_MAX);
				strncpy(dest, strsep(&line, ";"), PATH_MAX);
				entry = filemap_entry_add(source);
				entry->dest = strdup(dest);
				entry->is_lib = 1;
				break;

			default:
				len = off = zlen = 0;
				LOG("-- add file %s --", line);
				strncpy(source, strsep(&line, ";"), PATH_MAX);
				zlen = atoi(strsep(&line, ";"));
				off = atoi(strsep(&line, ";"));
				len = atoi(strsep(&line, ";"));
				entry = filemap_entry_add(source);
				entry->zlen = zlen;
				entry->off = off;
				entry->len = len;
		}

		line = NULL;
		len = 0;
		count += 1;
	}

	fclose(f);
	LOG("-- %d entries read --", count);
}

int __android_open(const char *pathname, int flags, mode_t mode) {
	LOG("-- __android_open(%s) --", pathname);
	return open(pathname, flags, mode);
	//return open(mangle(pathname), flags, mode);
}

FILE *__android_fopen(const char *pathname, const char *mode) {
	LOG("-- __android_fopen(%s) --", pathname);
	filemap_entry_t *entry = find_file(pathname);
	if ( entry == NULL )
		return fopen(pathname, mode);
	if ( entry->is_dir )
		return fopen(basedir, mode);
	return cookie_open(entry, mode);
}

FILE *__android_freopen(const char *path, const char *mode, FILE *stream) {
	LOG("-- __android_freopen(%s) --", path);
	if ( stream != NULL )
		fclose(stream);
	return __android_fopen(path, mode);
}

void __android_fill_stat(filemap_entry_t *entry, struct stat *buf) {
	// manually fill the stat for this file
	buf->st_dev = 0;
	buf->st_ino = 0;
	buf->st_mode = S_IFREG | 0444;
	buf->st_uid = 1000;
	buf->st_gid = 1000;
	buf->st_rdev = 0;
	buf->st_size = entry->len;
	buf->st_blksize = 1;
	buf->st_blocks = 1 + (int)(entry->len / 512);
	buf->st_atime = 0;
	buf->st_mtime = 0;
	buf->st_ctime = 0;
}

int __android_stat(const char *path, struct stat *buf) {
	LOG("-- __android_stat(%s) --", path);
	filemap_entry_t *entry = find_file(path);
	if ( entry == NULL )
		return stat(path, buf);
	if ( entry->is_dir )
		return stat(basedir, buf);
	__android_fill_stat(entry, buf);
	return 0;
}

int __android_lstat(const char *path, struct stat *buf) {
	LOG("-- __android_lstat(%s) --", path);
	filemap_entry_t *entry = find_file(path);
	if ( entry == NULL )
		return lstat(path, buf);
	__android_fill_stat(entry, buf);
	return 0;
}

void * __android_dlopen(const char *filename, int flag) {
	char dest[PATH_MAX];
	LOG("-- __android_dlopen(%s) --", filename);
	filemap_entry_t *entry = find_file(filename);
	if ( entry == NULL )
		return dlopen(filename, flag);

	snprintf(dest, PATH_MAX, "%s/%s", libdir, entry->dest);
	LOG("  --> redirected to %s", dest);
	return dlopen(dest, flag);
}

int __android_access(const char *pathname, int mode) {
	LOG("-- __android_access(%s) --", pathname);
	filemap_entry_t *entry = find_file(pathname);
	if ( entry == NULL )
		return access(pathname, mode);
	if (mode & W_OK)
		return EACCES;
	return 0;
}

int __android_fstat(int fd, struct stat *buf) {
	LOG("-- __android_fstat(fd=%d, index=%d) --", fd, FFD(fd));
	if (! IS_FFD(fd))
		return fstat(fd, buf);
	filemap_fd_t *ffd = fds[FFD(fd)];
	if ( ffd == NULL )
		return -1;
	__android_fill_stat(ffd->entry, buf);
	return 0;
}

/**
long __android_ftell(FILE *stream) {
	LOG("-- __android_tell(stream=%p) --", stream);
	if (! IS_FFD(stream->_file))
		return ftell(stream);
	filemap_fd_t *ffd = fds[FFD(stream->_file)];
	if ( ffd == NULL )
		return -1;
	return ffd->off;
}
**/

// mem slot 0 - native DIR
// mem slot 1 - directory name
// mem slot 2 - current search
DIR *__android_opendir(const char *name) {
	LOG("-- __android_opendir(%s) --", name);
	void **mem = NULL;
	DIR* ret = NULL;
	filemap_entry_t *entry = find_dir(name);
	if ( entry == NULL ) {
		LOG("  --> native access");
		ret = opendir(name);
		if (ret == NULL)
			return NULL;
		mem = calloc(sizeof(void *) * 3, 1);
		mem[0] = ret;
		return (DIR *)mem;
	} else {
		LOG("  --> wrapped access");
		mem = calloc(sizeof(void *) * 3, 1);
		mem[1] = (void *)entry;
		mem[2] = (void *)entries;
		return (DIR *)mem;
	}
}

struct dirent *__android_readdir(DIR *dirp) {
	LOG("-- __android_readdir(%p) --", dirp);
	void **mem = (void **)dirp;
	char *source;
	static struct dirent d;
	filemap_entry_t *entry;
	filemap_entry_t *basedir;

	// native access
	if (mem[0] != NULL) {
		LOG("  --> native access");
		return readdir((DIR *)mem[0]);
	}

	LOG("  --> wrapped access");

	// search the next file in the directory
	basedir = (filemap_entry_t *)mem[1];
	entry = (filemap_entry_t *)mem[2];
	while ( entry != NULL ) {
		if ( strcmp(basedir->source, entry->source) != 0 )
			goto nextentry;

		source = (char *)entry->source + 1;
		LOG("  --> might found an entry <%s>", entry->source);

		if ( strchr(source, '/') != NULL )
			goto nextentry;

		LOG("  --> selected <%s>", entry->source);

		d.d_ino = 0;
		d.d_off = 0;
		d.d_reclen = sizeof(struct dirent);
		d.d_type = entry->is_dir ? DT_DIR : DT_REG;
		strncpy(d.d_name, entry->source, 256);

		mem[2] = entry->next;
		return &d;

nextentry:;
		entry = entry->next;
	}

	LOG("  --> wrapped access ( end )");
	return NULL;
}

int __android_closedir(DIR *dirp) {
	LOG("-- __android_closedir(%p) --", dirp);
	void **mem = (void **)dirp;
	int ret;

	// native access
	if (mem[0] != NULL) {
		LOG("  --> native access");
		ret = closedir((DIR *)mem[0]);
		free(mem);
		return ret;
	}

	free(mem);
	return 0;
}



// JNI Injection
#include <jni.h>

/* JNI-C++ wrapper stuff */
#ifndef _JNI_WRAPPER_STUFF_H_
#define _JNI_WRAPPER_STUFF_H_

#define SDL_JAVA_PACKAGE_PATH org_renpy_android
#define JAVA_EXPORT_NAME2(name,package) Java_##package##_##name
#define JAVA_EXPORT_NAME1(name,package) JAVA_EXPORT_NAME2(name,package)
#define JAVA_EXPORT_NAME(name) JAVA_EXPORT_NAME1(name,SDL_JAVA_PACKAGE_PATH)

#endif
JNIEXPORT void JNICALL
JAVA_EXPORT_NAME(PythonActivity_nativeRedirect) (JNIEnv* env, jobject thiz,
		jobject fd_sys, jlong off, jlong len,
		jstring j_files_directory, jstring j_libs_directory) {
	jboolean iscopy;
	const char *libs_directory = (*env)->GetStringUTFChars(env, j_libs_directory, &iscopy);
	const char *files_directory = (*env)->GetStringUTFChars(env, j_files_directory, &iscopy);

	LOG("-- init native redirect from java. --");

	if (fd_sys == NULL) {
		LOG("Invalid fd_sys passed, NULL !");
		return;
	}

	jclass fdClass = (*env)->FindClass(env, "java/io/FileDescriptor");
	if (fdClass == NULL) {
		LOG("Unable to find class for java/io/FileDescriptor!");
		return;
	}

	jfieldID fdClassDescriptorFieldID = (*env)->GetFieldID(env, fdClass, "descriptor", "I");
	if (fdClassDescriptorFieldID == NULL ) {
		LOG("Unable to find descriptor field in java/io/FileDescriptor");
		return;
	}

	jint fd = (*env)->GetIntField(env, fd_sys, fdClassDescriptorFieldID);
	int newfd = dup(fd);
	LOG("-- init with a new fd=%d off=%ld len=%ld --", newfd, off, len);
	fd_data = fdopen(newfd, "rb");
	fd_data_off = off;
	fd_data_len = len;

	int pagesize = sysconf(_SC_PAGESIZE);
	int adjust = off % pagesize;
	LOG("-- pagesize=%d adjust=%d", pagesize, adjust);
	off_t adj_off = off - adjust;
	size_t adj_len = len + adjust;

	fd_data_map = mmap(NULL, adj_len, PROT_READ, MAP_SHARED, newfd, adj_off);
	if ( fd_data_map == MAP_FAILED ) {
		LOG("Unable to map the file");
		return;
	}

	fd_data_map += adjust;

	__android_init(files_directory, libs_directory);
}
