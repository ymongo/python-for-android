import sys
import subprocess

def parse_signature(java, jni):
    if not jni.startswith('  Signature: '):
        print 'invalid signature'
        return
    jni = jni[13:]
    javas = java.split()

    if javas[0] in ('public', 'private', 'protected'):
        javas.pop(0)

    is_static = False
    if javas[0] == 'static':
        javas.pop(0)
        is_static = True

    if jni[0] == '(':
        if javas[0][0] == '{':
            return
        if javas[0] in ('public', 'private', 'protected'):
            javas.pop(0)
        # method
        if '(' in javas[0]:
            # constructor
            return ('constructor', '', jni)
        else:
            javas.pop(0)
        name = javas[0].split('(')[0]
        if is_static:
            return ('staticmethod', name, jni)
        return ('method', name, jni)
    else:
        # field
        if javas[0] in ('public', 'private', 'protected'):
            javas.pop(0)
        name = javas[1].split(';')[0]
        if is_static:
            return ('staticfield', name, jni)
        return ('field', name, jni)

def parse(filename):
    cmd = subprocess.Popen(['javap', '-s', filename], stdout=subprocess.PIPE)
    stdout = cmd.communicate()[0]
    lines = stdout.splitlines()[1:]

    line = lines.pop(0)
    if not line.startswith('public class') and not line.startswith('class'):
        print '-> not a public class, exit.'
        return []

    javaclass = line[13:].split('{')[0].split(' ')[0]
    pythonclass = javaclass.rsplit('.')[-1]

    members = []
    while len(lines) > 2:
        javasignature = lines.pop(0)
        jnisignature = lines.pop(0)
        member = parse_signature(javasignature, jnisignature)
        if member is None:
            continue
        members.append(member)

    return (javaclass, pythonclass, members)


def generate(defs):
    javaclass, pythonclass, members = defs
    output = '''
from java import MetaJavaClass, JavaClass, JavaMethod, \\
        JavaStaticMethod, JavaField, JavaStaticField

class {0!r}(JavaClass):
    __metaclass__ = MetaJavaClass
    __javaclass__ = '{1!r}'

'''.format(pythonclass, javaclass)

    pyclasses = {
            'method': 'JavaMethod',
            'staticmethod': 'JavaStaticMethod',
            'field': 'JavaField',
            'staticfield': 'JavaStaticField' }

    for member in members:
        tp, name, sig = member
        if tp == 'constructor':
            output += '    __javaconstructor__ = {0!r}\n'.format(sig)
            continue
        cls = pyclasses[tp]
        output += '    {0} = {1}({2!r})\n'.format(name, cls, sig)

    return output



if __name__ == '__main__':
    filename = sys.argv[1]
    if filename.endswith('.class'):
        filename = filename[:-6]
    print generate(parse(filename))
