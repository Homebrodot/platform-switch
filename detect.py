import os
import platform
import sys
import os.path


def is_active():
    return True


def get_name():
    return "Switch"


def can_build():
    # Check the minimal dependencies
    devkitpro = os.environ.get("DEVKITPRO", "/opt/devkitpro")

    if not os.path.exists(devkitpro):
        print("DEVKITPRO not found. Switch disabled.")
        return False

    if not os.path.exists("{}/devkitA64".format(devkitpro)):
        print("devkitA64 not found. Switch disabled.")
        return False

    if not os.path.exists("{}/portlibs/switch/bin/aarch64-none-elf-pkg-config".format(devkitpro)):
        print("aarch64-none-elf-pkg-config not found. Switch disabled.")
        return False

    if os.system("pkg-config --version > /dev/null"):
        print("pkg-config not found. Switch disabled.")
        return False
    return True

def get_opts():

    from SCons.Variables import BoolVariable, EnumVariable

    return [
        BoolVariable("use_sanitizer", "Use LLVM compiler address sanitizer", False),
        BoolVariable("use_leak_sanitizer", "Use LLVM compiler memory leaks sanitizer (implies use_sanitizer)", False),
        EnumVariable("debug_symbols", "Add debugging symbols to release builds", "yes", ("yes", "no", "full")),
        BoolVariable("separate_debug_symbols", "Create a separate file containing debugging symbols", False),
        BoolVariable("touch", "Enable touch events", True),
    ]

def get_flags():
    f = None

    if not force_builtin_flags():
        f = [
            ("tools", False),
            ("builtin_pcre2_with_jit", False),
            # Todo should probably figure out a way to not have these eventually:
            ("builtin_mbedtls", False),
            ("builtin_libogg", False),
            ("builtin_libpng", False),
            ("builtin_libvorbis", False),
            ("builtin_libtheora", False),
            ("builtin_wslay", False),
            ("builtin_miniupnpc", False),
        ]
    else:
        f = [
            ("tools", False),
            ("builtin_enet", True),  # Not in portlibs.
            ("builtin_squish", True),  # Not in portlibs.
            ("builtin_freetype", False),
            ("builtin_libogg", False),
            ("builtin_libpng", False),
            ("builtin_libtheora", False),
            ("builtin_libvorbis", False),
            ("builtin_wslay", False),
            ("builtin_mbedtls", False),
            ("builtin_miniupnpc", False),
            ("builtin_opus", False),
            ("builtin_pcre2", False),
            ("builtin_zlib", False),
            ("builtin_zstd", False),
        ]

    return f


def configure(env):
    if sys.platform == "cygwin":
        # To prevent "Argument list too long" error when building on windows
        # Note this is likely not needed on linux
        # Detection logic from https://github.com/conan-io/conan/issues/2638#issuecomment-377393270
        env["split_libmodules"] = True

    env["CC"] = "aarch64-none-elf-gcc"
    env["CXX"] = "aarch64-none-elf-g++"
    env["LD"] = "aarch64-none-elf-ld"

    ## Build type

    dkp = os.environ.get("DEVKITPRO")
    env["ENV"]["DEVKITPRO"] = dkp
    updated_path = "{}/portlibs/switch/bin:{}/devkitA64/bin:".format(dkp, dkp) + os.environ["PATH"]
    env["ENV"]["PATH"] = updated_path
    os.environ["PATH"] = updated_path  # os environment has to be updated for subprocess calls

    arch = ["-march=armv8-a", "-mtune=cortex-a57", "-mtp=soft", "-fPIE"]
    env.Prepend(CCFLAGS=arch + ["-ffunction-sections"])

    env.Prepend(CPPPATH=["{}/portlibs/switch/include".format(dkp)])
    env.Prepend(CPPFLAGS=["-isystem", "{}/libnx/include".format(dkp)])
    env.Prepend(CPPFLAGS=["-D__SWITCH__", "-DPOSH_COMPILER_GCC", "-DPOSH_OS_HORIZON", '-DPOSH_OS_STRING=\\"horizon\\"'])

    env.Append(LIBPATH=["{}/portlibs/switch/lib".format(dkp), "{}/libnx/lib".format(dkp)])
    env.Prepend(LINKFLAGS=arch + ["-specs={}/libnx/switch.specs".format(dkp)])

    env.Prepend(CPPPATH=["#platform/switch/compat"])

    if env["target"] == "release":
        # -O3 -ffast-math is identical to -Ofast. We need to split it out so we can selectively disable
        # -ffast-math in code for which it generates wrong results.
        if env["optimize"] == "speed":  # optimize for speed (default)
            env.Prepend(CCFLAGS=["-O3", "-ffast-math"])
        else:  # optimize for size
            env.Prepend(CCFLAGS=["-Os"])

        if env["debug_symbols"] == "yes":
            env.Prepend(CCFLAGS=["-g1"])
        if env["debug_symbols"] == "full":
            env.Prepend(CCFLAGS=["-g2"])

    elif env["target"] == "release_debug":
        if env["optimize"] == "speed":  # optimize for speed (default)
            env.Prepend(CCFLAGS=["-O2", "-ffast-math", "-DDEBUG_ENABLED"])
        else:  # optimize for size
            env.Prepend(CCFLAGS=["-Os", "-DDEBUG_ENABLED"])

        if env["debug_symbols"] == "yes":
            env.Prepend(CCFLAGS=["-g1"])
        if env["debug_symbols"] == "full":
            env.Prepend(CCFLAGS=["-g2"])

    elif env["target"] == "debug":
        env.Prepend(CCFLAGS=["-g3", "-DDEBUG_ENABLED", "-DDEBUG_MEMORY_ENABLED"])
        # env.Append(LINKFLAGS=['-rdynamic'])

    ## Architecture

    env["bits"] = "64"

    # leak sanitizer requires (address) sanitizer
    if env["use_sanitizer"] or env["use_leak_sanitizer"]:
        env.Append(CCFLAGS=["-fsanitize=address", "-fno-omit-frame-pointer"])
        env.Append(LINKFLAGS=["-fsanitize=address"])
        env.extra_suffix += "s"
        if env["use_leak_sanitizer"]:
            env.Append(CCFLAGS=["-fsanitize=leak"])
            env.Append(LINKFLAGS=["-fsanitize=leak"])

    env["RANLIB"] = "aarch64-none-elf-ranlib"
    env["AR"] = "aarch64-none-elf-ar"

    env.Append(CCFLAGS=["-pipe"])
    env.Append(LINKFLAGS=["-pipe"])

    ## Dependencies

    if env["touch"]:
        env.Append(CPPFLAGS=["-DTOUCH_ENABLED"])

    # freetype depends on libpng and zlib, so bundling one of them while keeping others
    # as shared libraries leads to weird issues
    if env["builtin_freetype"] or env["builtin_libpng"] or env["builtin_zlib"]:
        env["builtin_freetype"] = True
        env["builtin_libpng"] = True
        env["builtin_zlib"] = True

    if not env["builtin_freetype"]:
        env.ParseConfig("aarch64-none-elf-pkg-config freetype2 --cflags --libs")

    if not env["builtin_libpng"]:
        env.ParseConfig("aarch64-none-elf-pkg-config libpng --cflags --libs")

    if not env["builtin_enet"]:
        env.ParseConfig("aarch64-none-elf-pkg-config libenet --cflags --libs")

    if not env["builtin_squish"] and env["tools"]:
        env.ParseConfig("aarch64-none-elf-pkg-config libsquish --cflags --libs")

    if not env["builtin_zstd"]:
        env.ParseConfig("aarch64-none-elf-pkg-config libzstd --cflags --libs")

    # Sound and video libraries
    # Keep the order as it triggers chained dependencies (ogg needed by others, etc.)

    if not env["builtin_libtheora"]:
        env["builtin_libogg"] = False  # Needed to link against system libtheora
        env["builtin_libvorbis"] = False  # Needed to link against system libtheora
        env.ParseConfig("aarch64-none-elf-pkg-config theora theoradec --cflags --libs")
    else:
        list_of_x86 = ["x86_64", "x86", "i386", "i586"]
        if any(platform.machine() in s for s in list_of_x86):
            env["x86_libtheora_opt_gcc"] = True

    if not env["builtin_libvorbis"]:
        env["builtin_libogg"] = False  # Needed to link against system libvorbis
        env.ParseConfig("aarch64-none-elf-pkg-config vorbis vorbisfile --cflags --libs")

    if not env["builtin_opus"]:
        env["builtin_libogg"] = False  # Needed to link against system opus
        env.ParseConfig("aarch64-none-elf-pkg-config opus opusfile --cflags --libs")

    if not env["builtin_libogg"]:
        env.ParseConfig("aarch64-none-elf-pkg-config ogg --cflags --libs")

    if not env["builtin_mbedtls"]:
        # mbedTLS does not provide a pkgconfig config yet. See https://github.com/ARMmbed/mbedtls/issues/228
        env.Append(LIBS=["mbedtls", "mbedx509", "mbedcrypto"])
    #else:
    #    env.Prepend(CPPFLAGS=["-DMBEDTLS_NO_PLATFORM_ENTROPY"])

    if not env["builtin_wslay"]:
        env.ParseConfig("aarch64-none-elf-pkg-config libwslay --cflags --libs")

    if not env["builtin_miniupnpc"]:
        env.ParseConfig("aarch64-none-elf-pkg-config miniupnpc --cflags --libs")

    # On Linux wchar_t should be 32-bits
    # 16-bit library shouldn't be required due to compiler optimisations
    if not env["builtin_pcre2"]:
        env.ParseConfig("aarch64-none-elf-pkg-config libpcre2-32 --cflags --libs")

    ## Flags

    # Linkflags below this line should typically stay the last ones
    # if not env['builtin_zlib']:
    #    env.ParseConfig('aarch64-none-elf-pkg-config zlib --cflags --libs')

    env.Append(CPPPATH=["#platform/switch"])
    env.Append(
        CPPFLAGS=[
            "-DHOMEBREW_ENABLED",
            "-DHORIZON_ENABLED",
            # Note that this just makes the NetSocketPosix implementation go away, Networking will still work because of NetSocketHorizon!
            "-DUNIX_SOCKET_UNAVAILABLE",
            "-DOPENGL_ENABLED",
            "-DGLES_ENABLED",
            "-DGLES2_LOAD_EXT_NO_DLCFN_AVAILABLE",
            "-DS3TC_NOT_SUPPORTED",
            "-DENET_UNIX_ENABLED",
            "-DPTHREAD_ENABLED",
            "-DPTHREAD_NO_RENAME",
            "-DGDNATIVE_LINUX_BSD_WEB",
        ]
    )

    if env["module_database_sqlite_enabled"]:
        env.Append(
            CPPFLAGS=[
                "-DSQLITE_OS_OTHER=1",
                "-DSQLITE_NO_FCHOWN",
                "-DSQLITE_OMIT_WAL",
                "-DSQLITE_CORE",
                "-DSQLITE_OMIT_LOAD_EXTENSION",
                "-DSQLITE_ENABLE_FTS4",
                "-DSQLITE_THREADSAFE=0",
                "-DSQLITE_MAX_EXPR_DEPTH=0",
                "-DSQLITE_OMIT_DEPRECATED",
                "-DSQLITE_OMIT_SHARED_CACHE",
            ]
        )

    env.Append(LIBS=["EGL", "GLESv2", "glapi", "drm_nouveau", "nx"])

    # -lglad -lEGL -lglapi -ldrm_nouveau

# Make this return True in your fork to force all bultins to link dynamically forcibly
def force_builtin_flags():
    return False
