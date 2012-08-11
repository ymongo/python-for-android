include "jni.pxi"
from libc.stdlib cimport malloc, free

cdef class JavaObject(object):
    cdef jobject obj
    def __cinit__(self):
        self.obj = NULL

cdef class JavaClass(object):
    cdef JNIEnv *j_env
    cdef jclass j_cls
    cdef jobject j_self

    def __cinit__(self, *args):
        self.j_env = NULL
        self.j_cls = NULL
        self.j_self = NULL

    def __init__(self, *args):
        """Create java object, with arguments, arguments need to be in the order
        of the java method signature
        """
        super(JavaClass, self).__init__()
        self.resolve_class()
        self.resolve_methods()
        self.call_constructor(args)

    cdef parse_definition(self, definition):
        self.definition = definition
        args, ret = definition[1:].split(')')
        if args:
            args = args.split(';')
        else:
            args = []
        return ret, args

    cdef void call_constructor(self, args):
        cdef jvalue *j_args = NULL
        # get the constructor definition if exist
        definition = '()V'
        if hasattr(self, 'j_constructor'):
            definition = self.j_constructor
        d_ret, d_args = self.parse_definition(definition)
        if len(args) != len(d_args):
            raise Exception("Invalid call, number of argument mismatch for constructor")
        # convert python arguments to java arguments
        if len(args):
            j_args = <jvalue *>malloc(sizeof(jvalue) * len(d_args))
            assert(j_args != NULL)
            try:
                if self.populate_args(d_args, j_args, args) < 0:
                    return
            finally:
                free(j_args)
        # get the java constructor
        cdef jmethodID constructor = self.j_env[0].GetMethodID(
            self.j_env, self.j_cls, "<init>", <char *><bytes><str>definition)
        # create the object
        self.j_self = self.j_env[0].NewObjectA(self.j_env, self.j_cls, constructor, j_args)
        if j_args != NULL:
            free(j_args)

    cdef void resolve_class(self):
        # search the Java class, and bind to our object
        assert(hasattr(self, 'j_classname'))
        self.j_env = SDL_ANDROID_GetJNIEnv()
        assert(self.j_env != NULL)
        self.j_cls = self.j_env[0].FindClass(self.j_env, <char *><bytes>self.j_classname)
        assert(self.j_cls != NULL)

    cdef void resolve_methods(self):
        # search all the JavaMethod within our class.
        cdef JavaMethod jm
        for name in dir(self.__class__):
            value = getattr(self.__class__, name)
            if not isinstance(value, JavaMethod):
                continue
            jm = value
            jm.resolve_method(self, name)

    cdef int populate_args(self, list definition_args, jvalue *j_args, args):
        cdef JavaObject j_object
        for index, argtype in enumerate(definition_args):
            py_arg = args[index]
            if argtype == 'Z':
                j_args[index].z = py_arg
            elif argtype == 'B':
                j_args[index].b = py_arg
            elif argtype == 'C':
                j_args[index].c = py_arg
            elif argtype == 'S':
                j_args[index].s = py_arg
            elif argtype == 'I':
                j_args[index].i = py_arg
            elif argtype == 'J':
                j_args[index].j = py_arg
            elif argtype == 'F':
                j_args[index].f = py_arg
            elif argtype == 'D':
                j_args[index].d = py_arg
            elif argtype[0] == 'L':
                if argtype == 'Ljava/lang/String;':
                    if isinstance(py_arg, basestring):
                        j_args[index].l = self.j_env[0].NewStringUTF(self.j_env, <char *><bytes>py_arg)
                    else:
                        raise Exception("Not a correct type of string, must be an instance of str or unicode")
                else:
                    if not isinstance(py_arg, JavaObject):
                        raise Exception('JavaObject needed for argument {0}'.format(index))
                    j_object = py_arg
                    j_args[index].l = j_object.obj
            elif argtype[0] == '[':
                raise Exception("List arguments not accepted")
        return 0

cdef class JavaMethod(object):
    cdef jmethodID j_method
    cdef JavaClass jc
    cdef JNIEnv *j_env
    cdef jclass j_cls
    cdef jobject j_self
    cdef char *definition
    cdef object is_static
    cdef object definition_return
    cdef object definition_args

    def __cinit__(self, definition, **kwargs):
        self.j_method = NULL
        self.j_env = NULL
        self.j_cls = NULL

    def __init__(self, definition, **kwargs):
        super(JavaMethod, self).__init__()
        self.parse_definition(definition)
        self.is_static = kwargs.get('static', False)

    cdef resolve_method(self, JavaClass jc, bytes name):
        # called by JavaClass when we want to resolve the method name
        self.jc = jc
        self.j_env = jc.j_env
        self.j_cls = jc.j_cls
        self.j_self = jc.j_self
        if self.is_static:
            self.j_method = self.j_env[0].GetStaticMethodID(
                    self.j_env, self.j_cls, <char *>name, self.definition)
        else:
            self.j_method = self.j_env[0].GetMethodID(
                    self.j_env, self.j_cls, <char *>name, self.definition)
        assert(self.j_method != NULL)

    cdef void parse_definition(self, definition):
        self.definition = <char *><bytes>definition
        args, ret = definition[1:].split(')')
        if args:
            args = args.split(';')
        else:
            args = []
        self.definition_return = ret
        self.definition_args = args

    def error_if_null(self, value):
        if not value:
            raise Exception("Return value was NULL")

    def __call__(self, *args):
        # argument array to pass to the method
        cdef jvalue *j_args = NULL
        cdef list d_args = self.definition_args
        if len(args) != len(d_args):
            raise Exception("Invalid call, number of argument mismatch")
        if len(args):
            j_args = <jvalue *>malloc(sizeof(jvalue) * len(d_args))
            assert(j_args != NULL)
            try:
                if self.jc.populate_args(self.definition_args, j_args, args) < 0:
                    return
            finally:
                free(j_args)

        try:
            if self.is_static:
                return self.call_staticmethod(j_args)
            return self.call_method(j_args)
        finally:
            if j_args != NULL:
                free(j_args)

    cdef call_method(self, jvalue *j_args):
        cdef jboolean j_boolean
        cdef jbyte j_byte
        cdef jchar j_char
        cdef jshort j_short
        cdef jint j_int
        cdef jlong j_long
        cdef jfloat j_float
        cdef jdouble j_double
        cdef jobject j_object
        cdef char *c_str
        cdef bytes py_str
        cdef object ret = None
        cdef JavaObject ret_jobject

        # return type of the java method
        r = self.definition_return[0]

        # now call the java method
        if r == 'V':
            self.j_env[0].CallVoidMethodA(self.j_env, self.j_self, self.j_method, j_args)
        elif r == 'Z':
            j_boolean = self.j_env[0].CallBooleanMethodA(self.j_env, self.j_self, self.j_method, j_args)
            ret = True if j_boolean else False
        elif r == 'B':
            j_byte = self.j_env[0].CallByteMethodA(self.j_env, self.j_self, self.j_method, j_args)
            #self.error_if_null(ret)
            ret = <char>j_byte
        elif r == 'C':
            j_char = self.j_env[0].CallCharMethodA(self.j_env, self.j_self, self.j_method, j_args)
            #self.error_if_null(ret)
            ret = <char>j_char
        elif r == 'S':
            j_short = self.j_env[0].CallShortMethodA(self.j_env, self.j_self, self.j_method, j_args)
            #self.error_if_null(ret)
            ret = <short>j_short
        elif r == 'I':
            j_int = self.j_env[0].CallIntMethodA(self.j_env, self.j_self, self.j_method, j_args)
            #self.error_if_null(ret)
            ret = <int>j_int
        elif r == 'J':
            j_long = self.j_env[0].CallLongMethodA(self.j_env, self.j_self, self.j_method, j_args)
            #self.error_if_null(ret)
            ret = <long>j_long
        elif r == 'F':
            j_float = self.j_env[0].CallFloatMethodA(self.j_env, self.j_self, self.j_method, j_args)
            #self.error_if_null(ret)
            ret = <float>j_float
        elif r == 'D':
            j_double = self.j_env[0].CallDoubleMethodA(self.j_env, self.j_self, self.j_method, j_args)
            #self.error_if_null(ret)
            ret = <double>j_double
        elif r == 'L':
            # accept only string for the moment
            j_object = self.j_env[0].CallObjectMethodA(self.j_env, self.j_self, self.j_method, j_args)
            #self.error_if_null(ret)
            if r == 'Ljava/lang/String;':
                c_str = <char *>self.j_env[0].GetStringUTFChars(self.j_env, j_object, NULL)
                py_str = <bytes>c_str
                self.j_env[0].ReleaseStringUTFChars(self.j_env, j_object, c_str)
                ret = py_str
            else:
                ret_jobject = JavaObject()
                ret_jobject.obj = j_object
                ret = ret_jobject
        elif r == '[':
            # TODO array support
            raise NotImplementedError("Array arguments not implemented")
        else:
            raise Exception('Invalid return definition?')

        # free args
        if j_args != NULL:
            free(j_args)

        return ret

    cdef call_staticmethod(self, jvalue *j_args):
        cdef jboolean j_boolean
        cdef jbyte j_byte
        cdef jchar j_char
        cdef jshort j_short
        cdef jint j_int
        cdef jlong j_long
        cdef jfloat j_float
        cdef jdouble j_double
        cdef jobject j_object
        cdef char *c_str
        cdef bytes py_str
        cdef object ret = None
        cdef JavaObject ret_jobject

        # return type of the java method
        r = self.definition_return[0]

        '''
        print 'TYPE', r
        print 'jenv', 'ok' if self.j_env else 'nop'
        print 'jcls', 'ok' if self.j_cls else 'nop'
        print 'jmethods', 'ok' if self.j_method else 'nop'
        print 'jargs', 'ok' if j_args else 'nop'
        '''

        # now call the java method
        if r == 'V':
            self.j_env[0].CallStaticVoidMethodA(self.j_env, self.j_cls, self.j_method, j_args)
        elif r == 'Z':
            j_boolean = self.j_env[0].CallStaticBooleanMethodA(self.j_env, self.j_cls, self.j_method, j_args)
            ret = True if j_boolean else False
        elif r == 'B':
            j_byte = self.j_env[0].CallStaticByteMethodA(self.j_env, self.j_cls, self.j_method, j_args)
            #self.error_if_null(ret)
            ret = <char>j_byte
        elif r == 'C':
            j_char = self.j_env[0].CallStaticCharMethodA(self.j_env, self.j_cls, self.j_method, j_args)
            #self.error_if_null(ret)
            ret = <char>j_char
        elif r == 'S':
            j_short = self.j_env[0].CallStaticShortMethodA(self.j_env, self.j_cls, self.j_method, j_args)
            #self.error_if_null(ret)
            ret = <short>j_short
        elif r == 'I':
            j_int = self.j_env[0].CallStaticIntMethodA(self.j_env, self.j_cls, self.j_method, j_args)
            #self.error_if_null(ret)
            ret = <int>j_int
        elif r == 'J':
            j_long = self.j_env[0].CallStaticLongMethodA(self.j_env, self.j_cls, self.j_method, j_args)
            #self.error_if_null(ret)
            ret = <long>j_long
        elif r == 'F':
            j_float = self.j_env[0].CallStaticFloatMethodA(self.j_env, self.j_cls, self.j_method, j_args)
            #self.error_if_null(ret)
            ret = <float>j_float
        elif r == 'D':
            j_double = self.j_env[0].CallStaticDoubleMethodA(self.j_env, self.j_cls, self.j_method, j_args)
            #self.error_if_null(ret)
            ret = <double>j_double
        elif r == 'L':
            # accept only string for the moment
            j_object = self.j_env[0].CallStaticObjectMethodA(self.j_env, self.j_cls, self.j_method, j_args)
            #self.error_if_null(ret)
            if r == 'Ljava/lang/String;':
                c_str = <char *>self.j_env[0].GetStringUTFChars(self.j_env, j_object, NULL)
                py_str = <bytes>c_str
                self.j_env[0].ReleaseStringUTFChars(self.j_env, j_object, c_str)
                ret = py_str
            else:
                ret_jobject = JavaObject()
                ret_jobject.obj = j_object
                ret = ret_jobject
        elif r == '[':
            # TODO array support
            raise NotImplementedError("Array arguments not implemented")
        else:
            raise Exception('Invalid return definition?')

        # free args
        if j_args != NULL:
            free(j_args)

        return ret

