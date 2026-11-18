set -e
FONT=/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf
B="fontfile=$FONT:fontcolor=white:borderw=7:bordercolor=black:fontsize=70:line_spacing=12:x=(w-text_w)/2"
T="$B:y=230"; L="$B:y=1480"
# durées (s) de chaque image ; transition « pale de ventilateur » = xfade radial de 0,3 s
DUR=(2.2 1.4 1.4 1.4 2.0 3.2)
X=0.3
f=""
for i in 0 1 2 3 4 5; do
  d=${DUR[$i]}; n=$(echo "$d*30/1" | bc)
  f="$f[$i:v]scale=2160:-2,crop=2160:3840,zoompan=z='1+0.0008*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=$n:s=1080x1920:fps=30,setsar=1,format=yuv420p,trim=duration=$d,setpts=PTS-STARTPTS"
  case $i in 0) f="$f,drawtext=$T:textfile=t1.txt";; 4) f="$f,drawtext=$L:textfile=t5.txt:enable='gte(t,0.4)'";; 5) f="$f,drawtext=$T:textfile=t6.txt:enable='gte(t,0.6)'";; esac
  f="$f[v$i];"
done
off=0; prev=v0
for i in 1 2 3 4 5; do
  off=$(echo "$off+${DUR[$((i-1))]}-$X" | bc)
  f="$f[$prev][v$i]xfade=transition=radial:duration=$X:offset=$off[x$i];"; prev=x$i
done
f="${f%;}"
ffmpeg -v error -y -loop 1 -i img1.jpg -loop 1 -i img2.jpg -loop 1 -i img3.jpg -loop 1 -i img4.jpg -loop 1 -i img5.jpg -loop 1 -i img6.jpg -filter_complex "$f" -map "[$prev]" -t 10.1 -c:v libx264 -crf 20 -preset slow -movflags +faststart costumes-muet.mp4
d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 costumes-muet.mp4)
ffmpeg -v error -y -i costumes-muet.mp4 -i /mnt/project-files/sons/happyukulele.mp3 -filter_complex "[1:a]atrim=0.8,asetpts=PTS-STARTPTS,atrim=0:$d,afade=t=out:st=$(echo "$d-1"|bc):d=1[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 160k -shortest costumes-youtube.mp4
echo $d
