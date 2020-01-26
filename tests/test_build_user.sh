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
echo "User.init_build"
echo "User.init_build"
echo "Packages.pre_build"
echo "User.pre_build"
echo "Packages.build"
buildah run --user root $ctr -- mkdir -p /var/cache/apk
mkdir -p /test/apk
mount -o bind /test/apk $mnt/var/cache/apk
mounts=("$mnt/var/cache/apk" "${mounts[@]}")
buildah run $ctr -- ln -s /var/cache/apk /etc/apk/cache
old="$(find .cache/apk/ -name APKINDEX.* -mtime +3)"
if [ -n "$old" ] || ! ls .cache/apk/APKINDEX.*; then
    buildah run --user root $ctr -- apk update
else
    echo Cache recent enough, skipping index update.
fi
buildah run --user root $ctr -- apk upgrade
buildah run --user root $ctr -- apk add shadow
echo "User.build"
if buildah run $ctr -- id 1000; then
    i=$(buildah run $ctr -- id -n 1000)
    buildah run $ctr -- usermod --home-dir /app --no-log-init 1000 $i
else
    buildah run $ctr -- useradd --home-dir /app --uid 1000 app
fi
echo "User.post_build"
buildah config --user app $ctr