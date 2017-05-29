import sys
import io
import segmentio

pid = sys.argv[1]
line = int(sys.argv[2])
num_lines = int(sys.argv[3]) - int(sys.argv[2]) + 1
physical_file = sys.argv[4]

print "GET:", "pid", pid, "line", line, "num_lines", num_lines, "physical_file", physical_file

fio = io.open(physical_file, 'r', encoding='utf-8')
sio = segmentio.SegmentIO(fio, u'') 
seg = sio.get_segment(block_begin_line=line, block_num_lines=num_lines)

data = seg.block_data()
with io.open('termdemo_data/%s-block.txt' % pid, 'w', encoding='utf-8') as f: 
    f.write(data)
