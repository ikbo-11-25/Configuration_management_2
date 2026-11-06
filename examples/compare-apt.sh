#!/bin/sh
# Reference only: run inside Ubuntu with an unpacked noble/main amd64 Packages.
set -eu
if [ "$#" -ne 1 ] || [ ! -f "$1" ]; then
    printf '%s\n' 'Usage: sh examples/compare-apt.sh /path/to/Packages' >&2
    exit 2
fi

scratch=$(mktemp -d)
trap 'rm -rf -- "$scratch"' EXIT
mkdir -p "$scratch/lists/partial" "$scratch/empty" "$scratch/archives/partial"
index=archive.ubuntu.com_ubuntu_dists_noble_main_binary-amd64_Packages
cp -- "$1" "$scratch/lists/$index"
printf '%s\n' 'deb [arch=amd64] http://archive.ubuntu.com/ubuntu noble main' \
    > "$scratch/sources.list"
: > "$scratch/status"
cat > "$scratch/apt.conf" <<EOF
APT::Architecture "amd64";
Dir::Etc::main "/dev/null";
Dir::Etc::parts "$scratch/empty";
Dir::Etc::sourcelist "$scratch/sources.list";
Dir::Etc::sourceparts "$scratch/empty";
Dir::State::lists "$scratch/lists";
Dir::State::status "$scratch/status";
Dir::Cache::pkgcache "";
Dir::Cache::srcpkgcache "";
Dir::Cache::archives "$scratch/archives";
Debug::NoLocking "true";
EOF
export APT_CONFIG="$scratch/apt.conf" LC_ALL=C
apt-cache --version
for spec in hello=2.10-3build1 grep=3.11-4build1 sed=4.9-2build1; do
    name=${spec%%=*}
    printf '\n=== %s: mandatory relationships ===\n' "$spec"
    apt-cache --important depends "$name"
    printf '\n=== %s: simulated unpack order ===\n' "$spec"
    apt-get -s --no-install-recommends --no-install-suggests install "$spec"
    printf '\n=== %s: download URIs without downloading ===\n' "$spec"
    apt-get --print-uris --download-only --assume-yes --allow-unauthenticated \
        --no-install-recommends --no-install-suggests install "$spec"
    printf '\n=== %s: native DOT diagram ===\n' "$spec"
    apt-cache -o APT::Cache::GivenOnly=true dotty \
        "$name" libc6 libgcc-s1 gcc-14-base libpcre2-8-0 \
        libacl1 libselinux1
done
