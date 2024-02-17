# Pandemonium for Nintendo Switch (Homebrew)

<p style="vertical-align: middle;">
<img style="width: 48px;" src="logo.png" alt="Pandemonium Icon" title="Engine Icon"/>
This repository houses the platform code for the Nintendo Switch (Homebrew).
</p>

<p style="vertical-align: middle;">
<img style="width: 48px;" src="icon.jpg" alt="Nintendo Switch Logo" title="Platform Logo"/>
This branch is specific to the Pandemonium Engine.
</p>

## Compiling

1. Install the build tools: https://switch.homebrew.guide/homebrew_dev/introduction.html

2. Run a terminal that comes with the build tools.

3. I'ts probably a good idea to do an update:

``` pacman -Syu ```

4. Install dependencies:

Build tools:

``` pacman -S python scons ```

Libraries:

``` pacman -S switch-mesa switch-mbedtls switch-libogg switch-libpng  switch-libvorbis  switch-libtheora  switch-wslay switch-miniupnpc ```

5. Get a copy of the engine source:

``` git clone https://github.com/Relintai/pandemonium_engine.git ```

6. Go into the engine's platform folder:

``` cd pandemonium_engine/platform ```

7. Clone this repository, and make sure the final folder is names `switch`:

``` git clone https://github.com/Relintai/platform_homebrew_switch.git switch ```

8. Build using:

``` scons platform=switch ```

### Dynamically linking to builtin dependencies

Install all the dependencies that you want to dynamically link to using the `pacman -S <NAME>` command.

Note: At the time of this writing enet, and squish is not in the repositories.

If you want to dynamically link to every available dependency you can use the following command:

``` scons platform=switch builtin_freetype=no builtin_opus=no builtin_pcre2=no builtin_zlib=no builtin_zstd=no ```
