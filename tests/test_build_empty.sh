#/usr/bin/env bash
base="alpine"
repo="None"
mounts=()
umounts() {
    for i in "${mounts[@]}"; do
        umount $i
        mounts=("${mounts[@]/$i}")
    done
    buildah unmount $ctr
    trap - 0
}
trap umounts 0
ctr=$(buildah from $base)
mnt=$(buildah mount $ctr)