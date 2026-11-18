set -e
FONT=/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf
B="fontfile=$FONT:fontcolor=white:borderw=7:bordercolor=black:fontsize=70:line_spacing=12:x=(w-text_w)/2"
T="$B:y=230"; L="$B:y=1480"
P="setpts=PTS-STARTPTS,crop=1080:1920,unsharp=5:5:0.3,fps=30,setsar=1,format=yuv420p"
ffmpeg -v error -y -i plan1-chat-g42.mp4 -i plan2-corgi-g42.mp4 -i plan3-fete-g42.mp4 -i plan4-tortue-g42.mp4 -filter_complex "
[0:v]trim=end_frame=90,$P,drawtext=$T:textfile=t1.txt,drawtext=$L:textfile=t2.txt:enable='gte(t,1)'[a];
[1:v]trim=end_frame=80,$P,drawtext=$L:textfile=t3.txt[b];
[2:v]trim=end_frame=40,$P,drawtext=$L:textfile=t4.txt[c];
[3:v]trim=end_frame=105,$P,drawtext=$T:textfile=t5.txt:enable='gte(t,0.6)'[d];
[a][b][c][d]concat=n=4:v=1:a=0[v]" -map "[v]" -c:v libx264 -crf 21 -preset slow -movflags +faststart soiree-muet.mp4
d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 soiree-muet.mp4)
ffmpeg -v error -y -i soiree-muet.mp4 -i /mnt/project-files/sons/toccata0.ogg -filter_complex "[1:a]atrim=0:$d,afade=t=out:st=$(echo "$d-1.2"|bc):d=1.2,volume=1.2[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 160k -shortest soiree-youtube.mp4
echo $d
