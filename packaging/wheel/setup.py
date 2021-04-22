from setuptools import setup, Extension
from setuptools.command.install import install
from setuptools.command.sdist import sdist
from wheel.bdist_wheel import bdist_wheel

import subprocess
import sys
import getpass

def get_version():
    version = subprocess.check_output(['./genversion.sh', '--print-only'])
    version = version.decode()
    if version.startswith('v'):
        version = version[1:]
    version = version.split('-')[0]
    return version

def get_version_from_file():
    try:
        f = open('./bindings/python/VERSION')
        version = f.read().split('/n')[0]
        f.close()
        return version
    except:
        print('Failed to get version from file. Using unknown')
        return 'unknown'

def binary_exists(name):
    """Check whether `name` is on PATH."""
    from distutils.spawn import find_executable
    return find_executable(name) is not None

def check_cmake3(path):
    from distutils.spawn import find_executable
    args = (path, "--version")
    popen = subprocess.Popen(args, stdout=subprocess.PIPE)
    popen.wait()
    output = popen.stdout.read().decode("utf-8") 
    prefix_len = len( "cmake version " )
    version = output[prefix_len:].split( '.' )
    return int( version[0] ) >= 3

def cmake_exists():
    """Check whether CMAKE is on PATH."""
    from distutils.spawn import find_executable
    path = find_executable('cmake')
    if path is not None:
        if check_cmake3(path): return True, path
    path = find_executable('cmake3')
    return path is not None, path 

def is_rhel7():
    """check if we are running on rhel7 platform"""
    try:
      f = open( '/etc/redhat-release', "r" )
      txt = f.read().split()
      i = txt.index( 'release' ) + 1
      return txt[i][0] == '7'
    except IOError:
      return False
    except ValueError:
      return False

def has_devtoolset():
    """check if devtoolset-7 is installed"""
    import subprocess
    args = ( "/usr/bin/rpm", "-q", "devtoolset-7" )
    popen = subprocess.Popen(args, stdout=subprocess.PIPE)
    rc = popen.wait()
    return rc == 0

# def python_dependency_name( py_version_short, py_version_nodot ):
#     """ find the name of python dependency """
#     from distutils.spawn import find_executable
#     # this is the path to default python
#     path = find_executable( 'python' )
#     from os.path import realpath
#     # this is the real default python after resolving symlinks
#     real = realpath(path)
#     index = real.find( 'python' ) + len( 'python' )
#     # this is the version of default python
#     defaultpy = real[index:]
#     if defaultpy != py_version_short:
#       return 'python' + py_version_nodot
#     return 'python'

class CustomInstall(install):
    def run(self): 

        py_version_short = self.config_vars['py_version_short']
        py_version_nodot = self.config_vars['py_version_nodot']

        cmake_bin, cmake_path = cmake_exists()
        make_bin    = binary_exists( 'make' )
        comp_bin    = binary_exists( 'c++' ) or binary_exists( 'g++' ) or binary_exists( 'clang' )

        import pkgconfig
        zlib_dev     = pkgconfig.exists( 'zlib' )
        openssl_dev  = pkgconfig.exists( 'openssl' )
        uuid_dev     = pkgconfig.exists( 'uuid' )
        if is_rhel7:
          devtoolset7 = has_devtoolset()
          need_devtoolset = "true"
        else:
          devtoolset7 = True # we only care about devtoolset7 on rhel7
          need_devtoolset = "false"
        
        pyname = None
        if py_version_nodot[0] == '3':
            python_dev = pkgconfig.exists( 'python3' ) or pkgconfig.exists( 'python' + py_version_nodot );
            pyname = 'python3'
        else:
            python_dev = pkgconfig.exists( 'python' );
            pyname = 'python'

        missing_dep = not ( cmake_bin and make_bin and comp_bin and zlib_dev and openssl_dev and python_dev and uuid_dev and devtoolset7 )

        if missing_dep:
          print( 'Some dependencies are missing:')
          if not cmake_bin:    print('\tcmake (version 3) is missing!')
          if not make_bin:     print('\tmake is missing!')
          if not comp_bin:     print('\tC++ compiler is missing (g++, c++, clang, etc.)!')
          if not zlib_dev:     print('\tzlib development package is missing!')
          if not openssl_dev:  print('\topenssl development package is missing!')
          if not python_dev:   print('\t{} development package is missing!'.format(pyname) )
          if not uuid_dev:     print('\tuuid development package is missing')
          if not devtoolset7:  print('\tdevtoolset-7 package is missing')
          raise Exception( 'Dependencies missing!' )

        useropt = ''
        command = ['./install.sh']
        if self.user:
            prefix = self.install_usersite
            useropt = '--user'
        else:
            prefix = self.install_platlib
        command.append(prefix)
        command.append( py_version_short )
        command.append( useropt )
        command.append( cmake_path )
        command.append( need_devtoolset )
        rc = subprocess.call(command)
        if rc:
          raise Exception( 'Install step failed!' )


class CustomDist(sdist):
    def write_version_to_file(self):

        version = get_version()
        with open('bindings/python/VERSION', 'w') as vi:
            vi.write(version)
    
    def run(self):
        self.write_version_to_file()
        sdist.run(self)


class CustomWheelGen(bdist_wheel):
    # Do not generate wheel
    def run(self):
        pass

version = get_version_from_file()
setup_requires=[ 'pkgconfig' ]

setup( 
    name             = 'xrootd',
    version          = version,
    author           = 'XRootD Developers',
    author_email     = 'xrootd-dev@slac.stanford.edu',
    url              = 'http://xrootd.org',
    license          = 'LGPLv3+',
    description      = "XRootD with Python bindings",
    long_description = "XRootD with Python bindings",
    setup_requires   = setup_requires,
    cmdclass         = {
        'install':     CustomInstall,
        'sdist':       CustomDist,
        'bdist_wheel': CustomWheelGen
    }
)
