#!/usr/bin/env bash

set -e

BUILD_IMAGE_NAME="lambda-packager:latest"

docker build -t "${BUILD_IMAGE_NAME}" $(pwd)
docker run --rm -ti -v "$(pwd):/data" "${BUILD_IMAGE_NAME}"

[ -d package-env ] && rm -fr package-env
# End of file