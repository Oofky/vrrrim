# vrrrim
typeracer but for practising vim \
For: NUS Orbital 26 (Project Gemini) \
By: my mouse is cooking in swimming oil

## Aim
We hope to make learning Vim keystrokes fun and engaging by having a platform where Vim learners can polish their skills without the added pressure of writing ‘good’ code, while simplifying the Vim learning process by having supporting features such as an accessible cheatsheet.

## Motivation
CS students using Vim for the first time are usually too focused on writing working code for assignments, such that there's no mental bandwidth left to memorise and practise keystrokes. This makes learning Vim properly difficult since the shortcuts do not commit to muscle memory. \
Therefore, we wanted to gamify the process of Vim navigation and text insertion and deletion with vrrrim, a TypeRacer-like game. This allows users to learn in a more engaging and enjoyable way, focusing on the application of Vim keybinds without the distraction of having to think of what code to write. \
Players need to reproduce a target file by making use of Vim shortcuts while racing others to be the first to fully replicate the file. The platform includes supportive features such as a cheatsheet that can be displayed during the game. \
Additionally, the platform highlights how mastering Vim can significantly improve coding efficiency. Players can observe how their speed improves as they refine their Vim skills and can also compare their performance with others through leaderboards, demonstrating the productivity benefits of becoming proficient in Vim.

## User Stories
1. As a student who wants to learn Vim keystrokes, I want to be able to quickly learn Vim in a convenient online environment, because opening a terminal and creating new text files can be slow.
2. As a student who wants to be quick at navigating and inserting code using Vim, I want to be able to practise my Vim skills, because practising on my assignments is difficult as I have to focus on writing proper code at the same time.
3. As someone with a 5-min break to play, I want to play quick games without having to wait too long, because I do not have much time.
4. As a particularly bored Internet user, I want to be able to have fun racing against other players online in this game, because competing against real players is thrilling and entertaining.
5. As a veteran at using Vim who wants to flex my skills, I want to be able to showcase my advanced Vim skills and feel a sense of achievement, because getting validation for my skills makes me happy.
6. As a player that plays at very odd times of the day, I want to be able to play singleplayer if there are not enough players online, because I want to practise my Vim skills without having to wait for players to come online.
7. As a player who is still unfamiliar with Vim, I want an easy way to refer to Vim keybinds, because this way I’ll still be able to experience the game despite my lower skill level.
8. As a player who wants to play with my friends, I want to be able to specifically race my friends instead of strangers, because I want to challenge my friends and have fun with them.

## Features
### Implemented:
#### Vim interface
An interface where players can type and edit code. This is the main input of the game. It includes two views: one showing the player’s current file and one showing the goal file that players need to replicate. Credit goes to CodeMirror for providing this functionality.
#### Comparison highlights
On the Vim interface, differences in code between the current file and the goal file are highlighted. This enables players to quickly identify where changes are needed (eg. lines where they should insert or delete code), so that they focus more on Vim navigation and insertion/deletion, rather than manually comparing both files and finding their differences. \
See the red and green comparison highlights. Credit goes to CodeMirror for providing this functionality.
#### Room codes with invite links
To join a race, players must be associated with a room code. This is to support the structure of our game: where many races will be happening with different people at the same time, some of which may be private races between friends. This is done by assigning each player a room code as part of their session data, which will then be used after they click ‘Play’ or ‘Create private room’ on the index page. \
If the player accesses the index page with a URL parameter (eg. /?aBc3Efgh), then the first parameter (aBc3Efgh) is seen as a room code. This implies that this player was sent a link by their friend to join their private race. If the room code is valid (ie. the room is open and can be found in our database), then they will be immediately assigned the room code. \
If the player accesses the index page without a URL parameter (e.g. /), they will not be assigned a room code yet. Previously assigned room codes will be cleared to prevent players from repeatedly joining the same room (which usually would be closed by the time they leave). \
Clicking ‘Create private room’ will always generate a new private room code and assign the player this room code, even if the player previously accessed the index page with a URL parameter (and thus had been assigned a room code already). They will be redirected to the private race with this room code. _The ‘private’ part of the code is not implemented yet. In the future, the room code will be stored in a database and tagged as private._ \
Clicking ‘Play’ can have different outcomes:
- If the player already has an assigned room code, they will be redirected to the race with this room code.
- Else, clicking ‘Play’ will find a public and open room, and assign the player its code. If no public and open rooms are available, one will be generated. The player is then redirected to the race with this room code. _Currently, clicking ‘Play’ without an assigned room code will always generate a new random code. This is to be changed in future milestones._
In the race, the invite link can be copied and shared to friends.
#### Progress bar
As this is a race, there needs to be an indicator for players to see how well they are doing against their fellow competitors during the race. This provides thrill and excitement during the race. This will be implemented in the form of multiple progress bars below the Vim interface, each representing one player’s progress towards replicating the target file. _Currently, only one progress bar is displayed because multiplayer races are not implemented yet._ \
Their progress towards replicating the target text is measured by comparing the Levenshtein distance (the difference between two sequences) between both texts. This distance is computed frequently to update the progress bar.
### To be implemented in future milestones:
#### Multiplayer race with auto-matchmaking
This game is designed with multiplayer in mind, as the game is about races. Ideally, races should have the size of 4-5 players. Most players will be looking for quick games rather than playing with friends, so auto-matchmaking will be necessary to quickly group players into rooms to play in races (considered as public rooms/races). \
There will be a countdown before the race automatically starts (even if there are not enough players, so some races may be singleplayer races), as it would create frustration and boredom when players are stuck in a room waiting for a race to start but no players join.
#### Vim cheatsheet
There should be an easily accessible tab for players to quickly refer to useful Vim keystrokes without affecting their view of the game. It should cater to beginners of Vim, thus including the basic keystrokes of Vim. Ideally, players will be able to customize their own cheatsheet such that they can note down specific keybinds that need more attention, thus catering to more intermediate learners of Vim as well.
#### Private races
Players will be able to create their own private rooms and invite their friends using a URL to race them.
#### Leaderboard and statistics 
The system will allow players to save their game statistics, such as the number of wins. Players are ranked on a leaderboard if they decide to upload their score. \
Other game statistics such as average speed (Levenshtein distance between the original text and the goal text / total time taken to complete the race) measured across time, displayed in a graph, will be useful for players to see how they improved over time, showcasing how coding can become more efficient with mastery of Vim.
#### Point deductions
Mouse clicks are generally undesirable when using Vim as there are always Vim shortcuts to achieve the same click faster. Each mouse click will thus deduct points from the player’s final score in the race. This incentivises using the keyboard and discourages use of the mouse.
#### Accounts
Players will be able to sign-up and log-in. Ideally, this will be done with as little information collected as possible, such as only usernames and passwords, making the process very fast and simple. This is because we want as many players to have an account as possible, so that they have access to leaderboards and statistics. However, perhaps emails may need to be collected so that players can reset their password in case they forget it, so that they do not lose their accounts and statistics. \
Accounts also allow for lasting customisation options, such as the colour of their car avatar (in the progress bar) in the game. Silly little customisation options like this can be fun for players.
