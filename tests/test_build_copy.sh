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
echo "Copy.init_build"
echo "Copy.build"
buildah run --user root $ctr -- mkdir -p /app
cp -a /home/jpic/src/podctl/tests $mnt/app