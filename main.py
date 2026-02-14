from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO, emit
import random
from string import ascii_uppercase
import base64
import os

def emit_qkd_debug(message, msg_type='info'):
    """Emit QKD debug messages to the client"""
    socketio.emit("qkd_debug", {"message": message, "type": msg_type}, room=request.sid)

# Create an instance of the app:
app = Flask(__name__)
app.config["SECRET_KEY"] = "very_secret_key" #TODO: See how to make this more secure
socketio = SocketIO(app)


rooms = {} # Stores information about existing rooms (codes & users)

# Funcition tot generate unique room code:
def generate_unique_code(length):
    # Do until valid code (not used yet) is generated:
    while True:
        # Keep appending "length" number of random uppercase letters:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)

        # Stop if the code is valid (not in rooms)
        if code not in rooms:
            break
    
    return code

# Function to generate a random bright color
# def generate_bright_color():
#     return "#{:02x}{:02x}{:02x}".format(random.randint(128, 255), random.randint(128, 255), random.randint(128, 255))


# Define routing for home page:
@app.route('/', methods=["GET", "POST"])
def home():
    # Clear session data:
    session.clear()
    # Wait for post request from front-end (after submission of form):
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False) # .get() function attempts to get a value from dictionary else returns None (but we set it to a default value of False, instead of None)
        create = request.form.get("create", False)

         # Check if user wants to create a room:
        if create != False:
            room = generate_unique_code(4)
            rooms[room] = {'members': 0, 'messages': [], 'users': [], 'creator': name}  # Initialize room
            session["is_new_room"] = True  # Add this flag to indicate a newly created room
    

        # Check if user didn't pass their name (regardless of joining or creating a room):
        if not name:
            return render_template("home.html", error="Please enter a name.", code=code, name=name) # To prevent removal of entered text (because post request refresh the page)

        # Check if user wants to join, but didn't provide a room code:
        if join != False and not code:
            return render_template("home.html", error="Please enter a room code.", code=code, name=name)

        # Normalize the room code to uppercase for storage and comparison
        room = code.upper() if code else None
        
        print(f"Attempting to join room: {room}")
        print(f"Available rooms: {rooms.keys()}")

        # Check if user wants to create a room:
        if create != False:
            room = generate_unique_code(4)
            rooms[room] = {'members': 0, 'messages': [], 'users': [], 'creator': name}  # Initialize 'users' and 'creator'
        
        # Else, if user wants to join a room with code:
        # 1) If invalid code:
        elif code.upper() not in rooms:
            return render_template("home.html", error="Room does not exist.", code=code, name=name)

        # 2) If valid code (or even in the case of creating a room):
        # Instead of advanced user authentication,
        # Use sessions that are semi-permanent user-data storage by server:
        # While running, use incognito tabs to have different sessions
        session["room"] = room
        session["name"] = name
        session["key"] = None #* Initialize with no key
        return redirect(url_for("room")) # Redirect to chatroom

    return render_template("home.html") # Render the HTML code for the home page
    #Note: no need to pass the name and code since this is for get requests only, not for posts, which refresh the page
    
# Define code & routing for chat room:
@app.route('/room', methods=["POST", "GET"])
def room():
    # To prevent user directly entering the /room without creating / joining a room:
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))

    return render_template("room.html", code=room, messages=rooms[room]["messages"]) # Render the HTML for the chat room

# Connect users to a chat room:
@socketio.on("connect") # Wait for connect request from the connected clients:
def connect(auth):
    print("\n[CONNECT] Socket connection initiated")
    print(f"[CONNECT] Request SID: {request.sid}")
    
    room = session.get("room")
    name = session.get("name")
    print(f"[CONNECT] Name: {name}, Room: {room}")
    
    # Check validity:
    if not room or not name:
        print("[CONNECT] Missing room or name, rejecting connection")
        return False
    
    # If joining an invalid room:
    is_new_room = session.get("is_new_room", False)
    if room not in rooms and not is_new_room:
        print(f"[CONNECT] Invalid room {room}, not in available rooms")
        leave_room(room)
        return False
    
    # Create the room if it's new and doesn't exist yet
    if room not in rooms and is_new_room:
        print(f"[CONNECT] Creating new room {room}")
        rooms[room] = {'members': 0, 'messages': [], 'users': [], 'creator': name}
        session.pop("is_new_room", None)  # Clear the flag after use
    
    print(f"[CONNECT] Valid room {room}, proceeding with QKD")
    
    # Ensure the room has a 'users' key
    if "users" not in rooms[room]:
        rooms[room]["users"] = []
        print("[CONNECT] Initialized users list for room")
    
    # Before QKD
    print("[CONNECT] Starting QKD protocol")
    
    #* Upon receiving connection request, simulate QKD and obtain keys, send back to client:
    '''
    MAJOR STEPS INVOLVED IN THE BB84 QKD PROTOCOL:
    1) DISTRIBUTING QUANTUM STATES
    2) SIFTING
    3) COMPUTING QBER
    4) INFORMATION RECONCILIATION (IF NOISY CHANNEL IS USED)
    5) PRIVACY AMPLIFICATION
    '''

    #####################################################################################################

    '''
    STEP 0: DEFINING HELPER FUNCTIONS:
    '''
    # Import all necessary objects and methods for quantum circuits
    from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit, qasm3
    from qiskit_aer import AerSimulator
    import random
    from random import randrange
    import hashlib

    # Code modified to introduce noise in communication channel:
    def NoisyChannel(qc1, qc2, qc1_name):
        ''' This function takes the output of a circuit qc1 (made up only of x and 
            h gates), simulate noisy quantum channel, where Pauli errors (X - bit flip; Z - phase flip
            will occur in qc2) and then initializes another circuit qc2 with introduce noise.
        ''' 
        
        # Quantum state is retrieved from qasm code of qc1:
        qs = qasm3.dumps(qc1).split(sep=';')[4:-1]

        # Process the code to get the instructions:
        for index, instruction in enumerate(qs):
            qs[index] = instruction.lstrip()

        # Parse the instructions and apply to new circuit:
        for instruction in qs:
            if instruction[0] == 'x':
                if instruction[5] == '[':
                    old_qr = int(instruction[6:-1])
                else:
                    old_qr = int(instruction[5:-1])
                qc2.x(qreg[old_qr])
            elif instruction[0] == 'h':
                if instruction[5] == '[':
                    old_qr = int(instruction[6:-1])
                else:
                    old_qr = int(instruction[5:-1])
                qc2.h(qreg[old_qr])
            elif instruction[0] == 'm': # exclude measuring:
                pass
            else:
                raise Exception('Unable to parse instruction')
        
        ### Introducing noise
        for instruction in qs:
            if randrange(7)<1:
                if instruction[5] == '[':
                    old_qr = int(instruction[6:-1])
                else:
                    old_qr = int(instruction[5:-1])
                qc2.x(qreg[old_qr]) #apply bit-flip error
            if randrange(7)<1:
                if instruction[5] == '[':
                    old_qr = int(instruction[6:-1])
                else:
                    old_qr = int(instruction[5:-1])
                qc2.z(qreg[old_qr]) #apply phase-flip error

    def print_outcomes_in_reverse(counts): # takes a dictionary variable
        for outcome in counts: # for each key-value in dictionary
            reverse_outcome = ''
            for i in outcome: # each string can be considered as a list of characters
                reverse_outcome = i + reverse_outcome # each new symbol comes before the old symbol(s)
        return reverse_outcome

    #####################################################################################################

    '''
    STEP 1: DISTRIBUTING QUANTUM STATES:
    '''
    emit_qkd_debug("🔄 STEP 1: Distributing Quantum States", "info")
    emit_qkd_debug(f"Initializing 24-qubit quantum register...", "info")

    qreg = QuantumRegister(24) # Quantum register with 24 qubits
    creg = ClassicalRegister(24) # Classical register with 24 bits

    send_list=[] # Initial bit string to send
    alice_basis=[] # Register to save information about encoding basis
    bob_basis=[] # Register to save information about decoding basis

    # Alice:
    alice = QuantumCircuit(qreg, creg, name='alice')

    for i in range(24):
        bit = randrange(2)
        send_list.append(bit)
    for i, n in enumerate(send_list):
        if n==1: alice.x(qreg[i]) # apply x-gate
    for i in range(24):
        r=randrange(2) # alice randomly picks a basis
        if r==0: # if bit is 0, then she encodes in Z basis
            alice_basis.append('Z')
        else: # if bit is 1, then she encodes in X basis
            alice.h(qreg[i])
            alice_basis.append('X')

    emit_qkd_debug(f"Alice's encoding bases: {alice_basis}", "info")
    emit_qkd_debug(f"Sending qubits through noisy channel...", "warning")

    bob = QuantumCircuit(qreg, creg, name='bob') # Defining Bob circuit
    NoisyChannel(alice, bob, 'alice') # Alice sends noisy states to bob

    emit_qkd_debug(f"Bob receiving and measuring qubits...", "info")

    # Bob:
    for i in range(24):
        r=randrange(2) # Bob randomly picks a basis
        if r==0: # if bit is 0, then measures in Z basis
            bob.measure(qreg[i],creg[i])
            bob_basis.append('Z')
        else: # if bit is 1, then measures in X basis
            bob.h(qreg[i])
            bob.measure(qreg[i],creg[i])
            bob_basis.append('X')

    emit_qkd_debug(f"Bob's measurement bases: {bob_basis}", "info")

    # Run the bob circuit:
    job = AerSimulator().run(bob, shots=1)
    counts = job.result().get_counts(bob)
    counts = print_outcomes_in_reverse(counts)
    received = list(map(int, counts))

    emit_qkd_debug(f"Bob's received bits: {received}", "info")

    #####################################################################################################

    '''
    STEP 2: SIFTING:
    '''
    emit_qkd_debug("🔄 STEP 2: Sifting Keys (Basis Reconciliation)", "info")
    
    # Sifting:
    alice_key=[] # Alice's register for matching rounds
    bob_key=[] # Bob's register for matching rounds
    for j in range(0,len(alice_basis)): # Going through list of bases 
        if alice_basis[j] == bob_basis[j]: # Comparing
            alice_key.append(send_list[j])
            bob_key.append(received[j]) # Keeping key bit if bases matched
        else:
            pass # Discard round if bases mismatched


    emit_qkd_debug(f"Matched bases: {len(alice_key)}/24", "success")
    emit_qkd_debug(f"Alice's sifted key: {alice_key}", "info")
    emit_qkd_debug(f"Bob's sifted key: {bob_key}", "info")

    #####################################################################################################

    '''
    STEP 3: COMPUTING QBER (QUANTUM BIT ERROR RATE):
    '''
    emit_qkd_debug("🔄 STEP 3: Computing QBER (Quantum Bit Error Rate)", "info")
    
    # QBER:
    rounds = len(alice_key)//3
    errors=0
    for i in range(rounds):
        bit_index = randrange(len(alice_key)) 
        tested_bit = alice_key[bit_index]
        if alice_key[bit_index]!=bob_key[bit_index]: # comparing tested rounds
            errors=errors+1 # calculating errors
        del alice_key[bit_index] # removing tested bits from key strings
        del bob_key[bit_index]
    QBER=errors/rounds # calculating QBER
    QBER=round(QBER,2) # saving the answer to two decimal places

    emit_qkd_debug(f"Tested {rounds} bits, found {errors} errors", "info")
    emit_qkd_debug(f"QBER = {QBER}", "success" if QBER < 0.11 else "warning")

    print("QBER value =", QBER)
    print("alices secret key =", alice_key)
    print("bob secret key =", bob_key)

    #####################################################################################################

    '''
    STEP 4: INFORMATION RECONCILIATION:

    4.1] CASCADE PROTOCOL
    4.2] BICONF STRATEGY
    '''

    def split(list1, n): 
        out = []
        last = 0.0
        while last < len(list1):
            out.append(list1[int(last):int(last + n)])
            last += n
        return out

    def cascade_pass(lA, lB, n): # input key lists A-alice, B-bob and target block size to divide in blocks
        # Shuffle:
        permutation = list(zip(lA, lB)) # map the index of multiple lists
        random.shuffle(permutation) # performing permutation
        shuffledLA, shuffledLB = zip(*permutation) # unpacking values
        # Split:
        splitLA=split(shuffledLA, n)
        splitLB=split(shuffledLB, n)
        # Calculate parity:
        # Creating empty lists, where "correctA/B" will include blocks with no error found
        # And "errorA/B" list with blocks where parities mismatched
        correctA, correctB, errorA, errorB= [], [], [], []
        sumBlocksA = [sum(block) for block in splitLA] # calculating parity by first calculating sums of each block in splitA/B
        sumBlocksB = [sum(block) for block in splitLB]
        parityA = [i %2 for i in sumBlocksA] # then applying mod(2) operator to our calculated sums and saving results
        parityB = [i %2 for i in sumBlocksB] # in parity bit list
        for i,value in enumerate(range(len(parityA))): # comparing parity bits from list1 with list2
            if parityA[i]==parityB[i]: # if parity bits matched - we add corresponding blocks to our list 'correct'
                correctA.append(splitLA[i])
                correctB.append(splitLB[i])
            else:
                errorA.append(splitLA[i]) # if parity bits mismatched - we add corresponding blocks to our list 'errors'
                errorB.append(splitLB[i])
        keyA = [item for i in correctA for item in i] # Converting our correct blocks into a list
        keyB= [item for i in correctB for item in i]
        return keyA, keyB, errorA, errorB # returning key that consist of correct blocks (list) and blocks with errors (tuple)

    '''
    4.1] CASCADING PROTOCOL:
    '''
    
    # Before starting error correction, we check calculated QBER value:
    if QBER==0.0:
        emit_qkd_debug("✅ QBER is 0 - Perfect channel! Skipping error correction.", "success")
        print("QBER is 0. Cascade Protocol skipped!")
        print("Final Key alice", alice_key)
        print("Final Key bob", bob_key)
    if QBER>=0.25: 
        emit_qkd_debug(f"❌ QBER threshold exceeded ({QBER} >= 0.25)", "error")
        emit_qkd_debug("Protocol aborted - channel too noisy!", "error")
        print("QBER value is", QBER,"\nThreshold value reached! Protocol Aborted!") # If QBER is above threshold value - we abort protocol
        #* Try again:
        connect(auth)
    if 0<QBER<=0.25: # if 0<QBER<=0.25 we perform Cascade protocol
        emit_qkd_debug("🔄 STEP 4: Error Correction (Cascade Protocol)", "info")
        blockSize=0.73//QBER
        emit_qkd_debug(f"Block size: {blockSize}", "info")
        kFinalA, kFinalB=[], [] # creating registers for final keys
        # Cascade protocol 1st pass:
        corrBlockA, corrBlockB, errBlockA, errBlockB=cascade_pass(alice_key, bob_key, blockSize) # cascade function
        kFinalA.extend(corrBlockA) # adding block which parity bits matched to final key string
        kFinalB.extend(corrBlockB)

        emit_qkd_debug(f"First pass complete - {len(errBlockA)} error blocks found", "info")
        
    # Now aproximately know how many errors we have in initial key string,
    # because after first pass each block in errorA/B list contains 1 (or other odd number) of errors
    # Now can determine the final (corrected) key list length before correcting those errors (when 1 bit is left in each block)
    # In other words, key length in penultimate pass of the Cascade protocol is known

        penultimatePassLength=len(alice_key)-len(errBlockA)
        pass_count = 1
        while len(kFinalA)!=penultimatePassLength: # Bisective search at each block until corrected key length is not equal length of initial key minus error blocks number after first pass
            pass_count += 1
            emit_qkd_debug(f"Cascade pass {pass_count} running...", "info")
            for i, (blockA, blockB) in enumerate(zip(errBlockA, errBlockB)):
                if len(blockA)>1:
                    secondPassA=list(blockA) # convert block into a lists
                    secondPassB=list(blockB)
                    blockSize2=len(blockA)//2 # change block size, now we will divide each block that contains an error in halfs
                    corrBlockA2, corrBlockB2,  errBlockA2, errBlockB2=cascade_pass(secondPassA, secondPassB, blockSize2) # and apply cascade
                    kFinalA.extend(corrBlockA2) # then add correct bits to key strings
                    kFinalB.extend(corrBlockB2)
                    errBlockA[i]=errBlockA2[0] # updating error block values
                    errBlockB[i]=errBlockB2[0]
                if len(blockA)==1: # Edge case if one block in the round will be shorter than the oner thus will require less passes
                    for bit in blockA:
                        if bit==1:
                            bitA=errBlockA[0][0]
                            kFinalA.append(bitA) # alice adds corresponding bit to her key string without change
                            bitB=errBlockB[0][0]+1 # but bob will first correct the error by flipping the bit value 
                            kFinalB.append(bitB)
                        if bit==0:
                            bitA=errBlockA[0][0]
                            kFinalA.append(bitA) # alice adds corresponding bit to her key string without change
                            bitB=errBlockB[0][0]-1 # but bob will first correct the error by flipping the bit value 
                            kFinalB.append(bitB)
                            
            #print("---PERFORMING NEXT PASS---\n", "Final key alice:", kFinalA, "\n", "Final key bob", kFinalB)
            #print(" Blocks with errors alice", errBlockA, "\n", "Blocks with errors bob", errBlockB)
            
        # After previous passes result is a nested lists, to convert them:    
        errorA=[item for elem in errBlockA for item in elem]
        errorB=[item for elem in errBlockB for item in elem]
        
        # Error correction step, when our error blocks contains just 1 bit (error)
        for i, error in enumerate(zip(errorA, errorB)):
    #       bitA=int(''.join(map(str, errorA))) # Converting tuple to integer
    #       bitB=int(''.join(map(str, errorB)))
            bitA=int(errorA[i])
            bitB=int(errorB[i])
            if bitA==1:
                kFinalA.append(bitA)
                correctedBitB=bitB+1
                kFinalB.append(correctedBitB)
            if bitA==0:
                kFinalA.append(bitA)
                correctedBitB=bitB-1
                kFinalB.append(correctedBitB)
                
        print("Final Key alice", kFinalA)
        print("Final Key bob", kFinalB)
        emit_qkd_debug(f"✅ Cascade complete after {pass_count} passes", "success")

    '''
    4.2] BICONF STRATEGY:
    '''
    emit_qkd_debug("🔄 Running BICONF strategy for additional error detection...", "info")

    from numpy import log as ln


    kFinalA=alice_key
    kFinalB=bob_key

    if QBER!=0: # defining size of blocks
        biconfBlockSize=(4*ln(2))//(3*QBER)
    if QBER==0:
        biconfBlockSize= min(8,len(kFinalA))
    # print(QBER)

    rounds = 0 # counting rounds
    biconfError=[] # creating register for rounds with an error
    error=0 # register for found and corrected error

    while rounds!=8: # we will go through rounds and monitor if blocks with errors will be found 
        rounds=rounds+1
        # Creating random subsets:
        kFinalZipped=list(zip(kFinalA, kFinalB)) # mapping indexes of our two lists
        randomBlock=random.sample(list(enumerate(kFinalZipped)), int(biconfBlockSize))
        # at this point there is nested tuple that contains (index of random bit, (bit from alice string, bit from bob string))
        #print(randomBitList) # will print out the nested tuple
        #print(randomBitList[0]) # will print out one block (index, (bitA, bitB))
        #print(randomBitList[0][0]) # will print only first pair index
        #print(randomBitList[0][1][0]) #will print only first pair alices' bit
        
        # To calculate and compare parity bits for both users bits:
        sumBlockA=0
        sumBlockB=0
        for i in range(0,int(biconfBlockSize)):
            sumBlockA=sumBlockA+randomBlock[i][1][0]
            sumBlockB=sumBlockB+randomBlock[i][1][1]
        parityA = sumBlockA%2 # then aplying mod(2) operator to the calculated sums and saving results
        parityB = sumBlockB%2
        
        if parityA!=parityB: # if parities of block dismatch - bisective search to correct error before continue with next round
            print("Error found in round:", rounds)
            print("Applying bisective search and error correction")
            # Applying bisective search to find and correct an error:
            while len(randomBlock)>1: # Take the block with error and run besective search till bit with error is found
                # Split the block:
                if len(randomBlock)%2==1: # If block size is odd
                    half=len(randomBlock)//2+1 # Length of our first block should be half+1
                else:
                    half=len(randomBlock)//2
                splitBlock=split(randomBlock, half) # spliting the block into two parts
                for i, block in enumerate(splitBlock): # For each part:
                    sumA=0
                    sumB=0
                    for j in range(0,len(block)): # calculating sums 
                        sumA=sumA+splitBlock[i][j][1][0]
                        sumB=sumB+splitBlock[i][j][1][1]
                    parA=sumA%2 # then calculate parities
                    parB=sumB%2
                    if parA==parB:
                        pass
                    if parA!=parB: # if parities dismatch- update our block and run while loop again
                        randomBlock=splitBlock[i]
            if len(randomBlock)==1: #once the error to 1 bit is isolated
                error=error+1
                print("Error found in bit:", randomBlock[0][0]) #  Retrieving the index of bit pair
                errorIndex=int(randomBlock[0][0])
                # Apply error correction at bob' initial key string:
            if kFinalB[errorIndex]==0:
                kFinalB[errorIndex]=1
            else:
                kFinalB[errorIndex]=0
            print("Error corrected!\n")
        else: # If parities matched
            pass

    print("BICONF strategy completed!\n", error, "errors found!")
    print("Final key alice", kFinalA)
    print("Final key bob", kFinalB)
    
    emit_qkd_debug(f"✅ BICONF complete - {error} errors found and corrected", "success")
    #####################################################################################################

    '''
    STEP 5: PRIVACY AMPLIFICATION: (THROUGH HASHING)
    '''

    emit_qkd_debug("🔄 STEP 5: Privacy Amplification (Hashing)", "info")

    # Privacy amplification:
    # Generating seed (salt):
    seed=[]
    for i in kFinalA:
        a=randrange(2)
        seed.append(a)

    # Adding seeds to the keys:
    kFinalA.append(seed)
    kFinalB.append(seed)

    # Converting lists to strings:
    strKFinalA = ''.join([str(elem) for elem in kFinalA])
    strKFinalB = ''.join([str(elem) for elem in kFinalB])

    # Checking first bit to decide hash function to use:
    if kFinalA[0]==1:
        resultA=hashlib.sha256(strKFinalA.encode())
        print("alices' final key:", bin(int(resultA.hexdigest(), 16))[2:])
        emit_qkd_debug("Using SHA-256 hash function", "info")
    else:
        resultA=hashlib.sha3_256(strKFinalA.encode())
        print("alices' final key:", bin(int(resultA.hexdigest(), 16))[2:])
        emit_qkd_debug("Using SHA3-256 hash function", "info")

    print()
    if kFinalB[0]==1:
        resultB=hashlib.sha256(strKFinalB.encode())
        print("bob' final key:", bin(int(resultB.hexdigest(), 16))[2:])
    else:
        resultB=hashlib.sha3_256(strKFinalB.encode())
        print("bob' final key:", bin(int(resultB.hexdigest(), 16))[2:])

    final_key = bin(int(resultA.hexdigest(), 16))[2:]
    emit_qkd_debug(f"✅ Final key generated: {final_key[:32]}... ({len(final_key)} bits)", "success")
    emit_qkd_debug("🔐 QKD Protocol Complete - Secure channel established!", "success")
    
    #* Store user key:
    session["key"] = bin(int(resultA.hexdigest(), 16))[2:]
    #* Send back key to user for them to store:
    socketio.emit("key", session["key"], room=request.sid)

    # Assign a random bright color to the user
    # color = generate_bright_color()
    # user_info = {"name": name, "color": color}

    # # Else, join the valid room:
    # join_room(room)
    # send({"name": name, "message": "has entered the room."}, to=room) # Send a JSON message to all people in the room
    # rooms[room]["members"] += 1
    # rooms[room]["users"].append(name)
    # emit("updateUserList", {"users": rooms[room]["users"], "creator": rooms[room]["creator"]}, to=room)
    # emit("setUserName", {"name": name}, room=request.sid)
    # print(f'{name} joined room {room}')
    # Else, join the valid room:
    # join_room(room)
    # send({"name": name, "message": "has entered the room."}, to=room) # Send a JSON message to all people in the room
    # rooms[room]["members"] += 1
    # rooms[room]["users"].append(name)
    # socketio.emit("key", session["key"], room=request.sid) # Emit the key (already present)
    # emit("setUserName", {"name": name}, room=request.sid) # Emit setUserName first
    # emit("updateUserList", {"users": rooms[room]["users"], "creator": rooms[room]["creator"]}, to=room) # Then emit updateUserList
    # print(f'{name} joined room {room}')
    # return True
    # After QKD
    print(f"[CONNECT] QKD complete, key generated: {session['key'][:10]}...")
    
    print(f"[CONNECT] Joining room {room}")
    join_room(room)
    
    print(f"[CONNECT] Incrementing member count and adding user to list")
    rooms[room]["members"] += 1
    rooms[room]["users"].append(name)
    
    print(f"[CONNECT] Emitting key to user")
    socketio.emit("key", session["key"], room=request.sid)
    
    print(f"[CONNECT] Emitting setUserName event")
    emit("setUserName", {"name": name}, room=request.sid)
    
    print(f"[CONNECT] Sending entry message to room")
    send({"name": name, "message": "has entered the room."}, to=room)
    
    print(f"[CONNECT] Updating user list")
    emit("updateUserList", {"users": rooms[room]["users"], "creator": rooms[room]["creator"]}, to=room)
    
    print(f"[CONNECT] {name} successfully joined room {room}")
    return True

# # Disconnecting users from the chat:
# @socketio.on("disconnect")
# def disconnect():
#     room = session.get("room")
#     name = session.get("name")
#     leave_room(room)

@socketio.on("disconnect")
def disconnect():
    print("\n[DISCONNECT] Socket disconnect initiated")
    room = session.get("room")
    name = session.get("name")
    print(f"[DISCONNECT] Name: {name}, Room: {room}")
    
    if not room or not name:
        print("[DISCONNECT] Missing room or name, early return")
        return
    
    leave_room(room)
    print(f"[DISCONNECT] Left room {room}")

    # Decrement member count of room:
    if room in rooms:
        print(f"[DISCONNECT] Updating room data")
        rooms[room]["members"] -= 1
        print(f"[DISCONNECT] New member count: {rooms[room]['members']}")
        
        rooms[room]["users"] = [user for user in rooms[room]["users"] if user != name]
        print(f"[DISCONNECT] Remaining users: {rooms[room]['users']}")
        
        # If the creator leaves, assign the next user as the new creator
        if rooms[room]["creator"] == name and rooms[room]["users"]:
            rooms[room]["creator"] = rooms[room]["users"][0]
            print(f"[DISCONNECT] New creator: {rooms[room]['creator']}")
        
        if rooms[room]["members"] <= 0:
            print(f"[DISCONNECT] Room {room} is empty, deleting")
            del rooms[room]
        else:
            print(f"[DISCONNECT] Emitting updated user list")
            emit("updateUserList", {"users": rooms[room]["users"], "creator": rooms[room]["creator"]}, to=room)

    # Send a message to all people in the room:
    print(f"[DISCONNECT] Sending departure message")
    send({"name": name, "message": "has left the room"}, to=room)
    print(f"[DISCONNECT] {name} has left the room {room}")

@socketio.on("requestUserList")
def request_user_list():
    room = session.get("room")
    if room and room in rooms:
        emit("updateUserList", {"users": rooms[room]["users"], "creator": rooms[room]["creator"]}, room=request.sid)



# Receive messages and send to all clients:
# XOR decryption function (keeps binary output)
def xor_decrypt(encrypted_message, key):
    # Base64 decode the message first
    decoded_message = base64.b64decode(encrypted_message)
    
    # XOR decryption
    result = ''.join(chr(decoded_message[i] ^ ord(key[i % len(key)])) for i in range(len(decoded_message)))
    return result

@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return

    # Retrieve binary key from session and convert it to ASCII
    binary_key = session.get("key")
    print('Binary key received from client:', binary_key)
    key = ''.join([chr(int(binary_key[i:i+8], 2)) for i in range(0, len(binary_key), 8)])  # Convert binary key to ASCII

    encrypted_message = data["message"]  # Get Base64 encoded message from client
    original_text = xor_decrypt(encrypted_message, key)  # Decrypt the message using XOR
    print('Decrypted original text:', original_text)
    
    content = {
        "name": session.get("name"),
        "message": original_text
    }

    send(content, to=room)  # Send decrypted message to the room
    rooms[room]["messages"].append(content)
    print(f'{session.get("name")} said: {original_text}')

@socketio.on("terminateRoom")
def terminate_room():
    room = session.get("room")
    name = session.get("name")

    if room in rooms and rooms[room]["creator"] == name:
        # Notify all users in the room
        emit("roomTerminated", {"code": room}, to=room)
        
        # Remove the room
        del rooms[room]
        print(f'Room {room} has been terminated by {name}')

# Get the host and port from environment variables
host = os.environ.get('HOST', '0.0.0.0')
port = int(os.environ.get('PORT', 5000))

if __name__ == "__main__":
    socketio.run(app, host=host, port=port, debug=True)

####################

