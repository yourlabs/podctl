#/usr/bin/env bash
base="alpine"
repo="None"
tag="None"
image="None"
mounts=()
umounts() {
    for i in "${mounts[@]}"; do
        umount $i
        echo $mounts
        mounts=("${mounts[@]/$i}")
        echo $mounts
    done
}
trap umounts 0
ctr=$(buildah from $base)
mnt=$(buildah mount $ctr)
mounts=("$mnt" "${mounts[@]}")