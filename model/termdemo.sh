#!/bin/sh

echo 'file:'
read FILE
echo "$FILE" > termdemo_data/filename-to-hash.txt
FILE_ID=`md5sum termdemo_data/filename-to-hash.txt | awk '{print $1;}'`
FILE_BASENAME="${FILE##*/}"

if [ ! -d "termdemo_data/$FILE_ID" ]
then 
    mkdir "termdemo_data/$FILE_ID"
    cp -l "$FILE" "termdemo_data/$FILE_ID/$FILE_BASENAME"
    cd "termdemo_data/$FILE_ID"
    git init
    git add "$FILE_BASENAME"
    git commit -m 'original file'
    cd -
    echo "[info] created new git repository in termdemo_data/$FILE_ID"
else
    echo "[info] we already have this file in termdemo_data/$FILE_ID"
fi

cd "termdemo_data/$FILE_ID"
MY_BASE_REVISION=`git rev-list HEAD | head -1`
cd -

CHANGELOG_FROM_HEAD_FILE="../$$-from-head.patch"
echo "[info] this process is editing revision $MY_BASE_REVISION"
echo "[info] changelog from HEAD in file: $CHANGELOG_FROM_HEAD_FILE"


echo 'first line:'
read FIRST_LINE
echo 'last line:'
read LAST_LINE


python termdemo-get.py "$$" "$FIRST_LINE" "$LAST_LINE" "termdemo_data/$FILE_ID/$FILE_BASENAME" # will put $$-block.txt
cp "termdemo_data/$$-block.txt" "termdemo_data/$$-block-src.txt"
vim "termdemo_data/$$-block.txt"  # here, while editing, the other users can also edit and save first

# now save:
cd "termdemo_data/$FILE_ID"
git diff --unified=0 "$HEAD_REVISION" "$MY_BASE_REVISION" > "$CHANGELOG_FROM_HEAD_FILE"
cd -

python termdemo-save.py "$$" "$FIRST_LINE" "$LAST_LINE"  "termdemo_data/$FILE_ID/$FILE_BASENAME" # will put $$-final.patch
cd "termdemo_data/$FILE_ID"
patch "$FILE_BASENAME" "../$$-final.patch"
git add "$FILE_BASENAME"
git commit -m "commit of process $$"
cd -

