# p2p-messenger

## Overview
finish this section

## Current Status
The project is currently ready to be presented; however the code has not been finalized for submission. Expect some edits over the next few days before the deadline (12/11).

### Features left to implement
* Client leaving the room
* Lamport clock for message catch-up

## How to Run
To run the **p2p-messanger** application, there are several steps.

1. Log into one of Notre Dame's student machines (i.e. `student10`, `student11`, etc).

2. Clone this repository.

3. Ensure a copy of `server.py` is running somewhere on the student machine. Either you, or someone else logged into this machine can do this:
  ```bash
  python3 server.py
  ```

4. **On the same student machine** (does not have to be the same terminal/VSCode session), run an instance of `client.py`:
```bash
python3 client.py
```

5. Follow the instructions given to you in the terminal, and chat away!

## Notes
Once you have entered a chatroom, typing /help into the terminal will give you a list of options.
 
