#!/bin/sh -x

USAGE="usage: ./deploy.sh USERNAME"

dev_dir=`pwd`
username="$1"
if [ -z "$username" ] 
then 
    echo "$USAGE"
    exit 1
fi

##### [begin configuration] #####
DEPLOY_DIR=/nlp/projekty/editor_korpusu/public_html/corpedit-devel
DEPLOY_ADDR="athena.fi.muni.cz"
##### [end configuration] #####

full_deploy_path="$username@$DEPLOY_ADDR:$DEPLOY_DIR"

rsync --delete -avp \
    --exclude=.git \
    --exclude=.pyc \
    --exclude=runtime_storage \
    --exclude=model/example_edited_files \
    --exclude=model/issues \
    --exclude=model/lockdir_testdata \
    --exclude=model/segmentio_testdata \
    --exclude=model/termdemo_data \
    --exclude=model/testdata_orig \
    --exclude=model/testdata_tmp \
    --exclude=log \
    "$dev_dir/" "$full_deploy_path/"


if ssh "$username@$DEPLOY_ADDR" "[ ! -d \"$DEPLOY_DIR/runtime_storage\" ]"
then 
    echo "creating runtime_storage dir..."
    ssh "$username@$DEPLOY_ADDR" "mkdir $DEPLOY_DIR/runtime_storage"
    ssh "$username@$DEPLOY_ADDR" "mkdir $DEPLOY_DIR/runtime_storage/edited_files"
    ssh "$username@$DEPLOY_ADDR" "mkdir $DEPLOY_DIR/runtime_storage/objects"
fi
if ssh "$username@$DEPLOY_ADDR" "[ ! -d \"$DEPLOY_DIR/log\" ]"
then 
    echo "creating log dir..."
    ssh "$username@$DEPLOY_ADDR" "mkdir $DEPLOY_DIR/log"
fi

# give the web server full access to everything 
ssh "$username@$DEPLOY_ADDR" "find $DEPLOY_DIR -exec setfacl -m u:www-data:rwx {} \;"

