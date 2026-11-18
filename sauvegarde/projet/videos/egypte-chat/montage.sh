set -e
FONT=/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf
T="fontfile=$FONT:fontcolor=white:borderw=7:bordercolor=black:fontsize=70:line_spacing=12:x=(w-text_w)/2:y=230"
P="setpts=PTS-STARTPTS,crop=1080:1920,unsharp=5:5:0.3,fps=30,setsar=1,format=yuv420p"
ffmpeg -v error -y -i plan1.mp4 -i plan2.mp4 -i plan3.mp4 -filter_complex "
[0:v]trim=end_frame=72,$P,drawtext=$T:textfile=t1.txt[a];
[1:v]$P,drawtext=$T:textfile=t1.txt:enable='lt(t,1.2)'[b];
[2:v]$P,drawtext=$T:textfile=t3.txt:enable='gte(t,1)'[c];
[a][b][c]concat=n=3:v=1:a=0[v]" -map "[v]" -c:v libx264 -crf 21 -preset slow -movflags +faststart egypte-muet.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 egypte-muet.mp4
