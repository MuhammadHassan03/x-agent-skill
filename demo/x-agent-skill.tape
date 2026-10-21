# VHS tape for the README demo. Render with: sh demo/render.sh   (see demo/README.md)
# Runs the real tools on the sample files in demo/samples. __PY__ is replaced by render.sh.
Output demo/x-agent-skill.gif

Set Shell "bash"
Set FontSize 16
Set Width 1200
Set Height 800
Set Padding 22
Set Theme "Dracula"
Set TypingSpeed 35ms
Set Framerate 14
Set PlaybackSpeed 1

Hide
Type "export PS1='$ '" Enter
Type "clear" Enter
Show

Type "__PY__ skills/x-post/postscore.py demo/samples/bait.txt" Sleep 400ms Enter
Sleep 4s

Hide
Type "clear" Enter
Show
Type "__PY__ skills/x-thread/thread.py demo/samples/long.txt" Sleep 400ms Enter
Sleep 4s

Hide
Type "clear" Enter
Show
Type "__PY__ skills/x-human/humanize.py demo/samples/slop.txt | tee /tmp/clean.txt" Sleep 400ms Enter
Sleep 3s
Type "__PY__ skills/x-human/detect.py demo/samples/slop.txt /tmp/clean.txt | tail -3" Sleep 400ms Enter
Sleep 5s
