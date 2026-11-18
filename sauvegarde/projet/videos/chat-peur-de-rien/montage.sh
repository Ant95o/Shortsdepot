set -e
UP="minterpolate=fps=32:mi_mode=mci:mc_mode=aobmc:vsbmc=1,scale=1108:1920:flags=lanczos,crop=1080:1920,unsharp=5:5:0.6"
for f in chat_a chat_b; do [ -f up_$f.mp4 ] || ffmpeg -v error -y -i $f.mp4 -vf "$UP" -c:v libx264 -crf 14 -preset fast -an up_$f.mp4; done
# halo orange pour la citrouille
ffmpeg -v error -y -f lavfi -i "color=c=black:s=240x240,format=rgba" -vf "geq=r=255:g=150:b=30:a='160*pow(max(0\,1-hypot(X-120\,Y-120)/120)\,1.3)'" -frames:v 1 halo.png
FONT=/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf
T="fontfile=$FONT:fontcolor=white:borderw=7:bordercolor=black:fontsize=78:x=(w-text_w)/2"
TC=2.1875; CX=628; CY=1262
ffmpeg -v error -y -i up_chat_a.mp4 -i up_chat_b.mp4 -loop 1 -i halo.png -filter_complex "
[0:v]setpts=PTS-STARTPTS,fps=32,drawtext=$T:y=300:textfile=t1.txt:enable='lt(t,4.6)'[a];
[1:v]split=3[b0][bz][br];
[b0]trim=0:$TC,setpts=PTS-STARTPTS[b1];
[bz]trim=start=$TC,setpts=PTS-STARTPTS,select=eq(n\,0),loop=32:1:0,setpts=N/32/TB[zs];
[2:v]scale=380:380,format=rgba[h];
[zs][h]overlay=x=$CX-190:y=$CY-250:enable='gte(n,4)*not(between(n,11,12))':shortest=1,
 zoompan=z='if(lt(on,8),1+on*0.2,2.6)':x='max(0,min(iw-iw/zoom,$CX-iw/zoom/2+if(gte(on,8),10*sin(on*1.7),0)))':y='max(0,min(ih-ih/zoom,$CY-ih/zoom/2+if(gte(on,8),10*cos(on*2.3),0)))':d=1:s=1080x1920:fps=32,
 drawbox=c=white@0.8:t=fill:enable='between(n,8,9)',trim=end_frame=32,setpts=PTS-STARTPTS[z];
[br]trim=start=$TC,setpts=(PTS-STARTPTS)/1.6,fps=32,tpad=stop_mode=clone:stop_duration=0.9,drawtext=$T:y=300:textfile=t2.txt[r];
[a][b1][z][r]concat=n=4:v=1:a=0,format=yuv420p[v]" -map "[v]" -c:v libx264 -crf 17 -preset medium -r 32 muet_noaudio.mp4
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 muet_noaudio.mp4); echo dur $DUR
# toccata dès que le squelette se lève (1,0 s), coupée net au flash ; tonnerre calé sur le flash (5,06+2,19+0,25)
A=/mnt/project-files/sons
FL=$(python3 -c "print(5.0625+$TC+0.25)")
ffmpeg -v error -y -i muet_noaudio.mp4 -ss 0.8 -i $A/toccata0.ogg -ss 10.75 -i $A/tonnerre0.ogg -filter_complex "
[1:a]atrim=0:$(python3 -c "print($FL-1.0)"),afade=t=out:st=$(python3 -c "print($FL-1.15)"):d=0.15,adelay=1000|1000,volume=0.8[m];
[2:a]atrim=0:3.5,afade=t=out:st=2.5:d=1,adelay=$(python3 -c "print(int($FL*1000))")|$(python3 -c "print(int($FL*1000))")[t];
[m][t]amix=inputs=2:normalize=0:duration=longest,apad,atrim=0:$DUR,loudnorm=I=-14:TP=-1.5[out]" -map 0:v -map "[out]" -c:v copy -c:a aac -b:a 192k son.mp4
cp muet_noaudio.mp4 muet.mp4
