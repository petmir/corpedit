import sys
import io
import segmentio

pid = sys.argv[1]
line = int(sys.argv[2])
num_lines = int(sys.argv[3]) - int(sys.argv[2]) + 1
physical_file = sys.argv[4]

print "GET:", "pid", pid, "line", line, "num_lines", num_lines, "physical_file", physical_file

with io.open('termdemo_data/%s-from-head.patch' % pid, 'r', encoding='utf-8') as f: 
    changelog_from_head = segmentio.changelog_from_patch_file_content(f.read())
print "changelog from head"
print "---"
print changelog_from_head
print "---"

fio = io.open(physical_file, 'r', encoding='utf-8')
sio = segmentio.SegmentIO(fio, changelog_from_head) 
seg = sio.get_segment(block_begin_line=line, block_num_lines=num_lines)

with io.open('termdemo_data/%s-block.txt' % pid, 'r', encoding='utf-8') as f: 
    new_block_data = f.read()

seg.set_block_data(new_block_data)
sio.save_segment(seg)
final_changelog = sio.file_changelog()
with io.open('termdemo_data/%s-final.patch' % pid, 'w', encoding='utf-8') as f: 
    f.write(u'--- \n+++ \n')
    f.write(final_changelog)

with io.open('termdemo_data/%s-final.patch' % pid, 'r', encoding='utf-8') as f: 
    print "~~~"
    print f.read()
    print "~~~"
