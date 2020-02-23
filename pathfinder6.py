# The Ultimate BootRogue Pathfinder tool
# Author: XlogicX
# Taking trivial pursuits more serious than significant ones

#Unconditional imports
import time
import argparse

# Get a timestamp at the beginning of processing
start = time.time()

# Get customisation from user
parser = argparse.ArgumentParser(description='Ultimate BootRogue Pathfinder')
parser.add_argument('--start', help='This is the dungeon you\'re currently on', default='1', type=str)
parser.add_argument('--end', help='This is the dungeon that you\'d like to get to', default='13', type=int)
parser.add_argument('--paths', help='How many hops would you like to consider?', type=int)
parser.add_argument('--itemdepth', help='How many dungeon exits would you like to consider?', default='7', type=int)
parser.add_argument('--progress', help='Shows progress indicator for those long runs', action="store_true")
args = parser.parse_args()

# Sanity check for 'unroutable' starting dungeons
if int(args.start) in (11,68,21,32,60,14,84,16,74,76,78,80,90,94,99,114):
  print("This starting dungeon has no reliably predictable exits")
  quit()
elif int(args.start) in (10,24):
  print("This starting dungeon has too few exits to be useful")
  quit()

# Initialize choice for if user wants to see all paths up to n paths, or if they just
# to see the shortest path
if not args.paths:
  args.paths = 1
  shortest = True
else: shortest = False

# Conditionally setup input handler for if the user wants to see a progress indicator.
# This is only setup if the user uses the --progress argument and if pynput is an
# installed module. If pynput is not able to load, a message will be given to the user
# and the script will still work normally as if the --progress argument wasn't used
handler = 1                       # Assume handler is working
if args.progress == True:
  try:
    from pynput import keyboard
  except:
    handler = 0                   # But note if the handler isn't working
    args.progress = False         # Turn the option off, as if the user didn't use it
    print('Unable to use --progress, the pynput module is not installed')
else: handler = 0
# Routine to run if handler is invoked
def on_press(key):
  try: k = key.char    # Get a single character
  except: k = key.name # other keys
  if k in ['space']:   # Is it the space bar?
    print('\r' + ' ' * 80,end='')               # Clear the line
    if section == 'paths':                      # Do progress status on paths section if in it
      print('\r{:.10f}'.format(status),end='')  # Print the percentage completed
      try:  # doing try/except due to div/0 possibility
        time_left = ((time.time()-start)/status)*(100-status)   # calculate time remaining (seconds)
        print(' - Time Left {:.2f} minutes'.format(time_left/60),end='',flush=True) # display it in minutes
      except:
        pass  #Just don't display time remaining, if it's div/0 exception, too early to calc anyway
    # Same kind of thing as the 'paths' logic but for the deduplication part of the processing
    elif section == 'dedup':
      print('\r{:.10f}'.format((pidx/len(wanted_paths))*100),end='')
      try:
        time_left = ((time.time()-dstart)/((pidx/len(wanted_paths))*100))*(100-((pidx/len(wanted_paths))*100))
        print(' - Time Left {:.2f} minutes'.format(time_left/60),end='',flush=True)
      except:
        pass
if handler == 1:
  lis = keyboard.Listener(on_press=on_press)
  lis.start() # start to listen on a separate thread    

# Data for each of the 128 dungeons
#   Item 1: First route (other 128 routes can be calculated from the first and routeorder list)
#   Item 2: How many food items is in the dungeon
dungeonpaths = [[28,3],[68,2],[48,2],[28,2],[60,2],[68,2],[12,2],[84,3],[60,2],[28,2],[0,0],[12,0],
  [48,3],[0,0],[56,3],[0,0],[68,1],[68,1],[128,1],[64,1],[0,0],[128,1],[60,1],[0,0],[28,2],[60,1],
  [60,1],[128,1],[128,0],[128,1],[128,1],[0,0],[28,2],[48,1],[64,2],[48,1],[32,2],[128,1],[12,2],
  [60,1],[12,2],[48,1],[28,2],[60,1],[68,2],[60,1],[60,2],[12,2],[12,1],[68,1],[28,2],[32,2],
  [60,1],[12,12],[12,2],[48,1],[32,2],[128,0],[128,0],[0,0],[28,2],[60,1],[28,2],[28,2],[60,2],
  [28,2],[128,2],[0,0],[56,2],[56,2],[28,2],[128,1],[60,1],[0,0],[64,2],[0,0],[128,2],[0,0],[68,2],
  [0,0],[28,2],[60,1],[28,2],[0,0],[68,2],[12,2],[60,2],[12,1],[56,2],[0,0],[32,3],[100,2],[68,2],
  [0,0],[12,1],[28,12],[128,2],[68,12],[0,0],[60,1],[28,3],[104,2],[28,2],[68,2],[60,2],[100,2],
  [128,2],[60,1],[28,3],[68,2],[100,3],[100,2],[68,2],[0,0],[68,2],[12,0],[12,3],[28,12],[68,2],
  [100,2],[32,3],[12,1],[68,3],[64,2],[68,2],[28,1],[60,2],[128,12]]
# Route Order
routeorder = []
for i in range(128):
  routeorder.append(i+1)


# This is the recursive beast that discovers every possible route
def source_hunt(desired_maze,mazes_ins,progress,current_depth,depth,paths):
  global status   # Because keyboard handler uses it
  # Get the total amount of entries into current dungeon and note it for this layer of struct
  if args.progress == True: progress[current_depth][1] = len(mazes_ins[desired_maze])
  # for each entry into the current dungeon
  for entry in mazes_ins[desired_maze]:

    # This is the part where we do magic to see how far we've made it
    if args.progress == True:
      progress[current_depth][0] += 1   # Increment ratio (current/total) dungeons for this node in hiearchy
      # Get value of ratio of completed (not current) (so -1) top hiearchy dungeon list
      status = ((progress[0][0]-1) / progress[0][1]) * 100
      for idx, part in enumerate(progress):   # Now lets evaluate the ratios for each node (with their own weights)
        if idx != 0:                          # But don't evaluate if we are on the top node
          frac = progress[idx][0]             # current progress on node
          try:
            frac /= progress[idx][1]          # divided by total of current node
          except:
            pass
          for i in range(idx):                # Divide by all previous node totals
            try:
              frac /= progress[i][1]
            except:
              pass
          status += frac*100                  # Get proportional progress contribution for this node

    # paths for route = dungeon,rngs,score
    paths[current_depth] = [entry[0],entry[1],entry[2]]
    # If the routes of the full path get from start dungeon to end dungeon, add it to wanted_paths list
    wanted_path = []    #individual notes to build metadata on
    for path in paths:            # look at the data for each dungeon/node
      wanted_path.append(path)
      try:
        if path[0] == int(args.start):      # If dungeon is the starting dungeon
          total_cost = 0                    # then we have a full route, init the cost
          for cost in wanted_path:          # Add up the total cost of each route for full path
            total_cost += cost[2]
          wanted_path.insert(0,total_cost)  # Taking full route and putting total cost at start of data struct
          wanted_paths.append(wanted_path)  # Adding this route to the full list
          break
      except:
        pass
    current_depth += 1            # Next level of recursion
    if current_depth != depth:    # If we aren't out of our depth for recursion
      source_hunt(entry[0],mazes_ins,progress,current_depth,depth,paths)  # dive in again
    current_depth -= 1          # otherwise back out one and keep processing the list we're on
  # At this point in the function, we finished a list on a hiearchy, so reset which item we're on
  if args.progress == True: progress[current_depth][0] = 0

# Displaying our data is the easy part
def displaypath(path):
  totalscore = path.pop(0)  # Parse the total route score
  print(u'\u2140{}| '.format(totalscore),end='') # Large Sigma
  path.reverse()            # Get paths in correct left->right order
  # Loop to print each dungeon with it's recommended route items
  for idx, dungeon in enumerate(path):
    traps = int((dungeon[1]-dungeon[2])/2)  # calculate ideal traps to hit
    food = int(dungeon[1]-traps)            # calculate how much food we can get
    if idx != 0:
      print(u' \u2192 ', end='')  # right arrow
    # Unicodes from left to right: box, club, diamond, smaller sigma
    print(u'\u00A4{}:{}\u2663{}\u25C6\u03A3{}'.format(dungeon[0], food, traps,dungeon[1]),end='')
  print()

def path_pass(mazes_ins,mazes_outs):
  # Some globals due to not being able to pass to keyboard handler
  global status
  global wanted_paths
  global pidx
  global section
  global dstart

  # Initialize data/variables
  status = ''       # Percentage complete for path exploration section
  wanted_paths = [] # Data srtructure to hold valid routes
  pidx = 0          # Amount of iterations through deduping, globally used (keyboard handler needs this)
  progress = [[0,0] for i in range(args.paths)]   # list of ratio pairs for each level in hiearchy
  depth = args.paths  # How many nodes to consider in route
  current_depth = 0   # Initialize recursion depth
  paths = [[] for i in range(depth)]  # Datastructure for dungeon/rng/score values

  # Indicating that we are about to evaluate all of our routes
  section = 'paths'
  # Let user know we are about to do this if we care about --progress
  if args.progress == True: print("Exploring Paths\nPress space bar for progress updates",end='')
  # Enter the rabbit hole of recursion
  source_hunt(args.end,mazes_ins,progress,current_depth,depth,paths)

  dstart = time.time()  # New 'start' timestamp that represents starting the dedup'ing process
  section = 'dedup'
  if args.progress == True: print("\nRemoving Duplicate Paths\nPress space bar for progress updates",end='')
  uniq_paths = []                         # We just now want unique routes (there are duplicates currently)
  for idx, x in enumerate(wanted_paths):  # For all of the routes
    pidx = idx  # (globally) note which route number we're on (for progress status)
    if x not in uniq_paths:   # If we havne't seen the route yet
      uniq_paths.append(x)      # Add it to the list

  # Sort the list (Best to worst)
  section = 'none'   # Just that we aren't really noting this part for progress (it's fast anyway)
  if args.progress == True: print("\nSorting Paths")
  uniq_paths = sorted(uniq_paths, reverse=True) #For sorting of the total traversal score

  # Now we choose which routes to display
  printed_depth = 1
  # Display a route for all levels up to the max selected by --paths
  while printed_depth < (args.paths + 1):
    for path in uniq_paths:                 # For each of the routes
      if (len(path) - 1) == printed_depth:  # If the route is appropriate for our printable depth
        displaypath(path)                   # print it and
        break                                 # get out
    printed_depth += 1                    # On to the next printable depth (more nodes per route)

  # If there were any valid paths at all, return 1 (this used for auto scaling of nodes/itemdepth)
  if len(wanted_paths) != 0:
    return(1)

# In this section, we are goind to build a large data structure that will hold
# All of the dungeons that lead into a particular dungeon for all 128 dungeons (mazes_ins),
# and all exits from each dungeon (mazes_outs) as defined by how many exits we wish to see
# (from itemdepth) for a maximum of up to 128 possible routes outbound
mazes_outs = [[] for i in range(129)]
mazes_ins = [[] for i in range(129)]
for idx, dungeon in enumerate(dungeonpaths):  # Check routing for each dungeon
  nonull = 0 #Flag to track if dungeon is routable, but at least one item needs to be hit to get out
  for i in range(128):          # Analyze each of the 128 routes out
    if i >= args.itemdepth:     # stop analyzing when we hit item cap set by itemdepth
      break
    if dungeon[0] != 0:         # if the current dungeon is routable (some aren't)
      routeidx = routeorder.index(dungeon[0]) # Get the routeorder index starting at the first exit
    else:     # But if it's not routable, forget about the rest of this
      break
    # Check for routing that requires at least one item. No dungeon should be more than 3
    # for this elemnt (food count), if the datastructure has it at 10 or higher, the leading
    # '1' is a flag for being required to pass through at least one item in order to exit.
    # The number after the leading '1' is the actual food count
    if dungeon[1] > 9:  # So if the flag is seen
      nonull = 1        # We can't just exit without getting an item
      dungeon[1] -= 10  # Now get the real food count
    # Determine food and traps for this path
    if i > dungeon[1]:              # If the exit number is higher than our max food ammount
      foodnumber = dungeon[1]       # Then that is the food amount
      trapnumber = i - dungeon[1]   # The rest is traps
    else:                           # Otherwise
      foodnumber = i                  # The exit number is the food number
      trapnumber = 0                  # No traps yet
    items = foodnumber+trapnumber #total rng triggering events
    # Get the dungeon path outbound
    if routeidx + i > 127:  # If needed, overflow loop to actually loop around the values
      outmaze = routeorder[routeidx+i-128]  # Using our routeorder lookup table, get the exit
    else:
      outmaze = routeorder[routeidx+i]      # Using our routeorder lookup table, get the exit
    mazes_outs[idx+1].append([items,outmaze])   # Append rng# and exit to current dungeon data
    mazes_ins[outmaze].append([idx+1,items,foodnumber-trapnumber]) # Append dungeon,rng#,score to entry data
  if nonull == 1:
    mazes_outs[idx+1].pop(0)  # Remove the first item if it isn't possible

from pprint import pprint
#for idx,mazeout in enumerate(mazes_outs):
#  print("{} - {}".format(idx,mazeout))
#for idx,mazein in enumerate(mazes_ins):
#  print("{} - {}".format(idx,mazein))

# If we want to auto-scale (up) the node amount and item depth for only the best & shortest route
if shortest == True:
  print('Using multiple passes to select the shortest path from dungeon {} to dungeon {}...'.format(args.start,args.end))
  for j in range(128):                    # scale from 4-128 item depth until a hit
    args.itemdepth = j+4                     # Assign that item depth
    passcap = 10  # Put limit on nodes per route
    for i in range(passcap):                  # For each node amount 1-10 (until hit)
      args.paths = i+1  # assign the node amount
      result = path_pass(mazes_ins,mazes_outs)    # See if there's a result
      if result:                                  # If so, we're done, if not, scale up
        exit = True
        break
    if exit == True: break
# Otherwise, the user knows they want more data and they know the parameters going in (could run slower)
else:
  print('Calculating the various routes from dungeon {} to dungeon {}...'.format(args.start,args.end))  
  path_pass(mazes_ins,mazes_outs)
  finish = time.time() - start
  print('Finished in {:.2f} minutes'.format(finish/60))