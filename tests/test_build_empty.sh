#/usr/bin/env bash
mounts=()
umounts() {
    for i in "${mounts[@]}"; do
        umount $i
    done
}
trap umounts 0
ctr=$(buildah from $base)
mnt=$(buildah mount $ctr)
mounts=("$mnt" "${mounts[@]}")