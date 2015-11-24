{\rtf1\ansi\ansicpg1252\cocoartf1348\cocoasubrtf170
{\fonttbl\f0\fnil\fcharset0 Menlo-Regular;}
{\colortbl;\red255\green255\blue255;\red38\green38\blue38;\red245\green245\blue245;}
\margl1440\margr1440\vieww16980\viewh11280\viewkind0
\deftab720
\pard\pardeftab720\sl380

\f0\fs28 \cf2 \cb3 \expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 Swiss Tournament\
\
This program simulates the first two rounds of a Swiss Tournament. Each player will be assigned to another and a win and loss will be recorded. In the next round, a player with one win will play another player with one win. A player with one loss will play another player with one loss. \
\
1. Install Virtualbox\
\
2. Install Vagrant\
\
3. Clone course provided repo shell \
$ git clone https://github.com/p00gz/udacity-swiss-tournament.git\
$ cd udacity-swiss-tournament\
$ cd vagrant\
\
4. Execute Vagrant Box\
vagrant up\
vagrant ssh\
\
5. Enter tournament\
\
6. Initialize the database \
psql\
vagran=> tournament.sql\
\
7. Run the test file\
tournament_text.py\
\
8. Review results \
\
9. Shutdown vagrant\
vagrant halt\
\
}