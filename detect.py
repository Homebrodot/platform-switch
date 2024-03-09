import os
import platform
import sys
import os.path

tool_prefix = "aarch64-none-elf-"

def is_active():
    return True


def get_name():
    return "Nintendo Switch"


def can_build():
    disabled = False # Allow all errors to print before cancelling the build

    # Check the minimal dependencies
    devkitpro = os.environ.get("DEVKITPRO", "/opt/devkitpro")
    devkita64 = os.environ.get("DEVKITA64", "/opt/devkitpro/devkitA64")

    if not os.path.exists(devkitpro):
        print("DevkitPro not found. Nintendo Switch disabled.")
        disabled = True
    else:
        if not os.path.exists(devkita64):
            print("DEVKITA64 environment variable is not set correctly.")
            if not os.path.exists("{}/devkitA64".format(devkitpro)):
                print("DevkitA64 not found. Nintendo Switch disabled.")
                disabled = True
        if not os.path.exists("{}/portlibs/switch/bin/{}pkg-config".format(devkitpro, tool_prefix)):
            print(tool_prefix + "pkg-config not found. Nintendo Switch disabled.")
            disabled = True

    if os.system("pkg-config --version > /dev/null"):
        print("pkg-config not found. Nintendo Switch disabled.")
        disabled = True

    return not disabled


def get_opts():

    from SCons.Variables import BoolVariable, EnumVariable

    return [
        BoolVariable("use_sanitizer", "Use LLVM compiler address sanitizer", False),
        BoolVariable("use_leak_sanitizer", "Use LLVM compiler memory leaks sanitizer (implies use_sanitizer)", False),
        BoolVariable("touch", "Enable touch events", True),
        EnumVariable("debug_symbols", "Add debugging symbols to release builds", "yes", ("yes", "no", "full")),
    ]


def get_flags():
    return [
        # Target build options
        ("tools", False), # Editor is not yet supported on Switch

        # Thirdparty libraries
        ## Found in portlibs:
        ("builtin_bullet", True), # Godot likes to depend on really new versions of bullet.
        ("builtin_enet", False), # switch-enet
        ("builtin_freetype", False), # switch-freetype
        ("builtin_libogg", False), # switch-libogg
        ("builtin_libpng", False), # switch-libpng
        ("builtin_libtheora", False), # switch-libtheora
        ("builtin_libvorbis", False), # switch-libvorbis
        ("builtin_libvpx", False), # switch-libvpx
        ("builtin_libwebp", False), # switch-webp
        ("builtin_wslay", False), # switch-wslay
        ("builtin_mbedtls", False), # switch-mbedtls
        ("builtin_miniupnpc", False), # switch-miniupnpc
        ("builtin_opus", False), # switch-libopus + switch-opusfile
        ("builtin_pcre2", False), # switch-libpcre2
        ("builtin_zlib", False), # switch-zlib
        ("builtin_zstd", False), # switch-zstd
    ]


def configure(env):
    env["CC"] = tool_prefix + "gcc"
    env["CXX"] = tool_prefix + "g++"
    env["LD"] = tool_prefix + "ld"

    ## Build type

    dkp = os.environ.get("DEVKITPRO")
    dka64 = os.environ.get("DEVKITA64")
    if not dka64:
        dka64 = "{}/devkitA64".format(dkp)
    env["ENV"]["DEVKITPRO"] = dkp
    updated_path = "{}/portlibs/switch/bin:{}/bin:".format(dkp, dka64) + os.environ["PATH"]
    env["ENV"]["PATH"] = updated_path
    os.environ["PATH"] = updated_path  # os environment has to be updated for subprocess calls

    arch = ["-march=armv8-a", "-mtune=cortex-a57", "-mtp=soft", "-fPIE"]
    env.Prepend(CCFLAGS=arch + ["-ffunction-sections"])

    env.Prepend(CPPPATH=["{}/portlibs/switch/include".format(dkp)])
    env.Prepend(CPPFLAGS=["-isystem", "{}/libnx/include".format(dkp)])
    env.Prepend(CPPDEFINES=[
        "__SWITCH__",
        "POSH_COMPILER_GCC",
        "POSH_OS_HORIZON",
        'POSH_OS_STRING=\\"horizon\\"'
    ])

    env.Append(LIBPATH=["{}/portlibs/switch/lib".format(dkp), "{}/libnx/lib".format(dkp)])
    env.Prepend(LINKFLAGS=arch + ["-specs={}/libnx/switch.specs".format(dkp)])

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
        env.Append(CPPDEFINES=["DEBUG_ENABLED"])
        if env["optimize"] == "speed":  # optimize for speed (default)
            env.Prepend(CCFLAGS=["-O2", "-ffast-math"])
        else:  # optimize for size
            env.Prepend(CCFLAGS=["-Os"])

        if env["debug_symbols"] == "yes":
            env.Prepend(CCFLAGS=["-g1"])
        if env["debug_symbols"] == "full":
            env.Prepend(CCFLAGS=["-g2"])

    elif env["target"] == "debug":
        env.Append(CPPDEFINES=["DEBUG_ENABLED", "DEBUG_MEMORY_ENABLED"])
        env.Prepend(CCFLAGS=["-g3"])
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

    if env["use_lto"]:
        env.Append(CCFLAGS=["-flto"])
        if env.GetOption("num_jobs") > 1:
            env.Append(LINKFLAGS=["-flto=" + str(env.GetOption("num_jobs"))])
        else:
            env.Append(LINKFLAGS=["-flto"])

        env["RANLIB"] = tool_prefix + "gcc-ranlib"
        env["AR"] = tool_prefix + "gcc-ar"
    else:
        env["RANLIB"] = tool_prefix + "ranlib"
        env["AR"] = tool_prefix + "ar"

    env.Append(CCFLAGS=["-pipe"])
    env.Append(LINKFLAGS=["-pipe"])

    ## Dependencies

    if env["touch"]:
        env.Append(CPPDEFINES=["TOUCH_ENABLED"])

    # freetype depends on libpng and zlib, so bundling one of them while keeping others
    # as shared libraries leads to weird issues
    if env["builtin_freetype"] or env["builtin_libpng"] or env["builtin_zlib"]:
        env["builtin_freetype"] = True
        env["builtin_libpng"] = True
        env["builtin_zlib"] = True

    if not env["builtin_freetype"]:
        env.ParseConfig(tool_prefix + "pkg-config freetype2 --cflags --libs")

    if not env["builtin_libpng"]:
        env.ParseConfig(tool_prefix + "pkg-config libpng --cflags --libs")

    if not env["builtin_bullet"]:
        # We need at least version 2.88
        import subprocess

        bullet_version = subprocess.check_output([tool_prefix + "pkg-config", "bullet", "--modversion"]).strip()
        if str(bullet_version) < "2.88":
            # Abort as system bullet was requested but too old
            print(
                "Bullet: System version {0} does not match minimal requirements ({1}). Aborting.".format(
                    bullet_version, "2.88"
                )
            )
            sys.exit(255)
        env.ParseConfig(tool_prefix + "pkg-config bullet --cflags --libs")

    if not env["builtin_enet"]:
        env.ParseConfig(tool_prefix + "pkg-config libenet --cflags --libs")

    if not env["builtin_squish"] and env["tools"]:
        env.ParseConfig(tool_prefix + "pkg-config libsquish --cflags --libs")

    if not env["builtin_zstd"]:
        env.ParseConfig(tool_prefix + "pkg-config libzstd --cflags --libs")

    # Sound and video libraries
    # Keep the order as it triggers chained dependencies (ogg needed by others, etc.)

    if not env["builtin_libtheora"]:
        env["builtin_libogg"] = False  # Needed to link against system libtheora
        env["builtin_libvorbis"] = False  # Needed to link against system libtheora
        env.ParseConfig(tool_prefix + "pkg-config theora theoradec --cflags --libs")
    else:
        list_of_x86 = ["x86_64", "x86", "i386", "i586"]
        if any(platform.machine() in s for s in list_of_x86):
            env["x86_libtheora_opt_gcc"] = True

    if not env["builtin_libvpx"]:
        env.ParseConfig(tool_prefix + "pkg-config vpx --cflags --libs")

    if not env["builtin_libvorbis"]:
        env["builtin_libogg"] = False  # Needed to link against system libvorbis
        env.ParseConfig(tool_prefix + "pkg-config vorbis vorbisfile --cflags --libs")

    if not env["builtin_opus"]:
        env["builtin_libogg"] = False  # Needed to link against system opus
        env.ParseConfig(tool_prefix + "pkg-config opus opusfile --cflags --libs")

    if not env["builtin_libogg"]:
        env.ParseConfig(tool_prefix + "pkg-config ogg --cflags --libs")

    if not env["builtin_libwebp"]:
        env.ParseConfig(tool_prefix + "pkg-config libwebp --cflags --libs")

    if not env["builtin_mbedtls"]:
        # mbedTLS does not provide a pkgconfig config yet. See https://github.com/ARMmbed/mbedtls/issues/228
        env.Append(LIBS=["mbedtls", "mbedx509", "mbedcrypto"])

    if not env["builtin_wslay"]:
        env.ParseConfig(tool_prefix + "pkg-config libwslay --cflags --libs")

    if not env["builtin_miniupnpc"]:
        env.ParseConfig(tool_prefix + "pkg-config miniupnpc --cflags --libs")

    # On Linux wchar_t should be 32-bits
    # 16-bit library shouldn't be required due to compiler optimisations
    if not env["builtin_pcre2"]:
        env.ParseConfig(tool_prefix + "pkg-config libpcre2-32 --cflags --libs")

    ## Flags

    # Linkflags below this line should typically stay the last ones
    # if not env['builtin_zlib']:
    #    env.ParseConfig(tool_prefix + 'pkg-config zlib --cflags --libs')

    env.Append(CPPPATH=["#platform/switch"])
    env.Append(CPPDEFINES=[
        "HOMEBREW_ENABLED",
        "HORIZON_ENABLED",
        "LIBC_FILEIO_ENABLED",
        "OPENGL_ENABLED",
        "GLES_ENABLED",
        "PTHREAD_ENABLED",
        "PTHREAD_NO_RENAME",
        ])
    env.Append(LIBS=["EGL", "GLESv2", "glapi", "drm_nouveau", "nx"])

    # -lglad -lEGL -lglapi -ldrm_nouveau
