set -e
FONT=/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf
T="fontfile=$FONT:fontcolor=white:borderw=7:bordercolor=black:fontsize=70:line_spacing=12:x=(w-text_w)/2"
UP="minterpolate=fps=32:mi_mode=mci:mc_mode=aobmc:vsbmc=1,crop=1080:1920,unsharp=5:5:0.4"
ffmpeg -v error -y -i plan1.mp4 -vf "trim=end_frame=101,setpts=PTS-STARTPTS,$UP" -c:v libx264 -crf 14 -preset fast up1.mp4
ffmpeg -v error -y -i plan2.mp4 -vf "trim=start_frame=6,setpts=PTS-STARTPTS,$UP" -c:v libx264 -crf 14 -preset fast up2.mp4
ffmpeg -v error -y -sseof -0.05 -i up2.mp4 -frames:v 1 fin.png
ffmpeg -v error -y -i up1.mp4 -i up2.mp4 -loop 1 -framerate 32 -i fin.png -filter_complex "
[0:v]setpts=PTS-STARTPTS,fps=32,setsar=1,format=yuv420p,drawtext=$T:y=260:textfile=t1.txt[a];
[1:v]setpts=PTS-STARTPTS,fps=32,setsar=1,format=yuv420p[b];
[2:v]zoompan=z='1+on*0.012':x='iw/2-iw/zoom/2':y='700-ih/zoom/2':d=1:s=1080x1920:fps=32,trim=end_frame=42,setpts=PTS-STARTPTS,setsar=1,format=yuv420p,drawtext=$T:y=260:textfile=t2.txt[c];
[a][b][c]concat=n=3:v=1:a=0,format=yuv420p[v]" -map "[v]" -c:v libx264 -crf 17 -preset medium -r 32 muet.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 muet.mp4
