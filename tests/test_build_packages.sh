#/usr/bin/env bash
base="alpine"
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
buildah run $ctr -- mkdir -p /var/cache/apk
mkdir -p $(pwd)/.cache/apk
mount -o bind $(pwd)/.cache/apk $mnt/var/cache/apk
mounts=("$mnt/var/cache/apk" "${mounts[@]}")
buildah run $ctr -- ln -s /var/cache/apk /etc/apk/cache
if [ -n "$(find .cache/apk/ -name APKINDEX.* -mtime +3)" ]; then
    buildah run $ctr -- apk update
fi
buildah run $ctr -- apk upgrade
buildah run $ctr -- apk add bash