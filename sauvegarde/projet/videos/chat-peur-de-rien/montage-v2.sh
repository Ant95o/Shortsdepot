set -e
FONT=/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf
T="fontfile=$FONT:fontcolor=white:borderw=7:bordercolor=black:fontsize=78:x=(w-text_w)/2"
TC=2.1875; CX=628; CY=1262
# fin Kaggle : chat qui panique (images 24-74), puis porche vide (image 115) tenu 1,3 s
[ -f up_fuite.mp4 ] || ffmpeg -v error -y -i fuite1.mp4 -vf "trim=start_frame=24:end_frame=75,setpts=PTS-STARTPTS,minterpolate=fps=32:mi_mode=mci:mc_mode=aobmc:vsbmc=1,crop=1080:1920,unsharp=5:5:0.4" -c:v libx264 -crf 14 -preset fast up_fuite.mp4
ffmpeg -v error -y -sseof -0.05 -i up_chat_b.mp4 -frames:v 1 vide.png
ffmpeg -v error -y -i up_chat_a.mp4 -i up_chat_b.mp4 -loop 1 -i halo.png -i up_fuite.mp4 -loop 1 -t 1.3 -framerate 32 -i vide.png -filter_complex "
[0:v]setpts=PTS-STARTPTS,fps=32,drawtext=$T:y=300:textfile=t1.txt:enable='lt(t,4.6)'[a];
[1:v]split=2[b0][bz];
[b0]trim=0:$TC,setpts=PTS-STARTPTS[b1];
[bz]trim=start=$TC,setpts=PTS-STARTPTS,select=eq(n\,0),loop=32:1:0,setpts=N/32/TB[zs];
[2:v]scale=380:380,format=rgba[h];
[zs][h]overlay=x=$CX-190:y=$CY-250:enable='gte(n,4)*not(between(n,11,12))':shortest=1,
 zoompan=z='if(lt(on,8),1+on*0.2,2.6)':x='max(0,min(iw-iw/zoom,$CX-iw/zoom/2+if(gte(on,8),10*sin(on*1.7),0)))':y='max(0,min(ih-ih/zoom,$CY-ih/zoom/2+if(gte(on,8),10*cos(on*2.3),0)))':d=1:s=1080x1920:fps=32,
 drawbox=c=white@0.8:t=fill:enable='between(n,8,9)',trim=end_frame=32,setpts=PTS-STARTPTS[z];
[3:v]setpts=PTS-STARTPTS,fps=32,setsar=1[f];
[4:v]fps=32,format=yuv420p,setsar=1,drawtext=$T:y=300:textfile=t2.txt[e];
[a][b1][z][f][e]concat=n=5:v=1:a=0,format=yuv420p[v]" -map "[v]" -c:v libx264 -crf 17 -preset medium -r 32 muet.mp4
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 muet.mp4); echo dur $DUR
FD=$(ffprobe -v error -show_entries format=duration -of csv=p=0 up_fuite.mp4); echo fuite $FD
A=/mnt/project-files/sons
FL=$(python3 -c "print(5.0625+$TC+0.25)")
HS=$(python3 -c "print(int((5.0625+$TC+1.0+(63-24)/24-0.08)*1000))")
ffmpeg -v error -y -i muet.mp4 -ss 0.8 -i $A/toccata0.ogg -ss 10.75 -i $A/tonnerre0.ogg -ss 0.9 -i $A/feulement3.wav -filter_complex "
[1:a]atrim=0:$(python3 -c "print($FL-1.0)"),afade=t=out:st=$(python3 -c "print($FL-1.15)"):d=0.15,adelay=1000|1000,volume=0.8[m];
[2:a]atrim=0:3.0,afade=t=out:st=2.0:d=1,adelay=$(python3 -c "print(int($FL*1000))")|$(python3 -c "print(int($FL*1000))")[t];
[3:a]atrim=0:1.2,afade=t=out:st=1.0:d=0.2,adelay=$HS|$HS,volume=1.6[s];
[m][t][s]amix=inputs=3:normalize=0:duration=longest,apad,atrim=0:$DUR,loudnorm=I=-14:TP=-1.5[out]" -map 0:v -map "[out]" -c:v copy -c:a aac -b:a 192k son.mp4
