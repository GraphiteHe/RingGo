import pygame
import keyboard
import random
import threading 

pygame.init()
pygame.mixer.init()
sound=pygame.mixer.Sound('./sounds/click.ogg')

screen=pygame.display.set_mode((720, 720))
clock=pygame.time.Clock()
board_size,line_width,bg_color,grid_color=19,2,(217,175,109),(0,0,0)
board,valid,ko_temp,dead_temp,color_temp,mouse_state,current_move,keyboard_state,was_pressed=[],[],None,[],1,0,None,[0,0,0,0],0
with open('./settings.txt','r') as file:
    text=file.read().split('\n')
board_size=int(text[0])
game_mode=int(text[1])
inv_amount=int(text[2])

for i in range(board_size):
    board.append(list([0]*board_size))
    valid.append(list([1]*board_size))

def pos(item):
    return (72+576*item[0]/(board_size-1),72+576*item[1]/(board_size-1))

def draw_element(board_size=board_size,line_width=2,grid_color=(0,0,0)):
    board_surface=pygame.surface.Surface((720,720))
    board_surface.fill(bg_color)
    for i in range(board_size):
        pygame.draw.line(board_surface,grid_color,(72+576*i/(board_size-1),72),(72+576*i/(board_size-1),648),line_width)
        pygame.draw.line(board_surface,grid_color,(72,72+576*i/(board_size-1)),(648,72+576*i/(board_size-1)),line_width)
    for i in range(board_size):
        for j in range(board_size):
            if valid[i][j]==0:
                pygame.draw.rect(board_surface,bg_color,(pos([i,j])[0]-576/(board_size-1)+line_width,pos([i,j])[1]-576/(board_size-1)+line_width,1152/(board_size-1)-line_width,1152/(board_size-1)-line_width))
    black_surface=pygame.image.load('./images/black.png')
    white_surface=pygame.image.load('./images/white.png')
    black_surface=pygame.transform.scale(black_surface,(576/(board_size-1),576/(board_size-1)))
    white_surface=pygame.transform.scale(white_surface,(576/(board_size-1),576/(board_size-1)))
    return board_surface,black_surface,white_surface
board_surface,black_surface,white_surface=draw_element(board_size=board_size,line_width=2,grid_color=(0,0,0))

def get_item():
    position=pygame.mouse.get_pos()
    if False: 
        return None###
    else:
        for i in range(0,board_size):
            for j in range(0,board_size):
                if abs(position[0]-pos([i,0])[0])<288/(board_size-1) and abs(position[1]-pos([0,j])[1])<288/(board_size-1):
                    if valid[i][j]==1:
                        return (i,j)

def left(l:list):
    try:
        l.append(list(l[0]))
    except:
        l.append(l[0])
    del l[0]
    return l
def right(l:list):
    try:
        l.insert(0,list(l[-1]))
    except:
        l.insert(0,l[-1])
    del l[-1]
    return l
def up(l:list):
    return list(map(lambda x:left(x),l))
def down(l:list):
    return list(map(lambda x:right(x),l))

def neighbors(item:list)->set:
    l=set()
    i,j=item[0],item[1]
    if game_mode==0:
        if i!=0:
            if valid[i-1][j]==1:
                l.add((i-1,j))
        if i!=board_size-1:
            if valid[i+1][j]==1:
                l.add((i+1,j))
        if j!=0:
            if valid[i][j-1]==1:
                l.add((i,j-1))
        if j!=board_size-1:
            if valid[i][j+1]==1:
                l.add((i,j+1))
    else:
        if valid[(i-1)%board_size][j%board_size]==1:
            l.add(((i-1)%board_size,j%board_size))
        if valid[(i+1)%board_size][j%board_size]==1:
            l.add(((i+1)%board_size,j%board_size))
        if valid[i%board_size][(j-1)%board_size]==1:
            l.add((i%board_size,(j-1)%board_size))
        if valid[i%board_size][(j+1)%board_size]==1:
            l.add((i%board_size,(j+1)%board_size))
    return l
def to_set(item):
    group=set()
    if type(item) is tuple:
        group.add(item)
    elif type(item) is set:
        group=item
    return group
def edge(item)->set:
    group=to_set(item)
    temp=set()
    for i in group:
        temp=temp|neighbors(i)
    return temp-group
def colored_edge(item,color)->set:
    group=to_set(item)
    stone_edge=edge(item)
    temp=set()
    for i in stone_edge:
        if board[i[0]][i[1]]==color:
            temp.add(i)
    return temp-group
def group(item,color)->set:
    group=to_set(item)
    while True:
        edge=colored_edge(group,color)
        group=edge|group
        if edge==set():
            return group
def liberties(item,color)->int:
    stone_group=group(item,color)
    stone_edge=edge(stone_group)
    liberties=0
    for i in stone_edge:
        if board[i[0]][i[1]]==0:
            liberties+=1
    return liberties
def is_valid(item:tuple,color:int):
    global death_temp,ko_temp
    if board[item[0]][item[1]]!=0:
        return False
    death_temp=set()
    for i in neighbors(item):
        if board[i[0]][i[1]]+color==0:
            if liberties(i,-color)<=1:
                death_temp=death_temp|group(i,-color)
    if len(death_temp)>1:
        ko_temp=None
        return True
    if len(death_temp)==1:
        if death_temp==to_set(ko_temp):
            return False
        ko_temp=item
        return True
    if liberties(item,color)==0:
        return False
    ko_temp=None
    return True
def evaluate(a):
    b=[]
    for i in range(0,board_size):
        b.append(list(a[i]))
    checked=list(map(lambda y:list(map(lambda x:abs(x),y)),b))
    for i in range(0,board_size):
        for j in range(board_size):
            if checked[i][j]==0 and valid[i][j]==1:
                stone_group=group((i,j),0)
                stone_edge=edge(stone_group)
                if stone_edge!=set():
                    bw=[0,0]
                    for k in stone_edge:
                        if b[k[0]][k[1]]==1:
                            bw[0]+=1
                        if b[k[0]][k[1]]==-1:
                            bw[1]+=1
                    if bw[0]==0:
                        for k in stone_group:
                            b[k[0]][k[1]]=-1
                    if bw[1]==0:
                        for k in stone_group:
                            b[k[0]][k[1]]=1
                for k in stone_group:
                    checked[k[0]][k[1]]=1
    return b

def spawn_board(inv_amount=inv_amount,mode=game_mode):
    global valid,board,board_size
    counter,valid,board=0,[],[]
    if mode==0:
        board_size+=2
        board.append(list([0]*(board_size)))
        for i in range(board_size-2):
            board.append(list([0]+[1]*(board_size-2)+[0]))
        board.append(list([0]*(board_size)))
        for i in range(board_size):
            valid.append(list([1]*(board_size)))
        while counter<inv_amount:
            stone_group=group((0,0),0)
            stone_edge=edge(stone_group)
            random_element=random.sample(list(stone_edge),1)[0]
            board[random_element[0]][random_element[1]]=0
            counter+=1
        board=list(board[1:-1])
        board=list(map(lambda x:list(x[1:-1]),board))
        valid=list(board)
        board=[]
        for i in range(board_size):
            board.append(list([0]*(board_size)))
        board_size-=2
    if mode==1:
        for i in range(board_size):
            valid.append(list([1]*(board_size)))
            board.append(list([0]*(board_size)))
        while counter<inv_amount:
            i=random.randint(0,board_size-1)
            j=random.randint(0,board_size-1)
            if valid[i][j]==1:
                valid[i][j]=0
                counter+=1
    

spawn_board()
board_surface,black_surface,white_surface=draw_element()
screen.fill(bg_color)
screen.blit(board_surface,(0,0))

pygame.display.flip()

while True:
    event=pygame.event.get()
    if keyboard.is_pressed('e'):
        keyboard_state=[0,0,0,0]
        mouse_state=0
        if was_pressed==0:
            stone=0
            eval=evaluate(list(board))
            screen.blit(board_surface,(0,0))
            for i in range(board_size):
                for j in range(board_size):
                    if board[i][j]==1:
                        position=pos([i,j])
                        screen.blit(black_surface,(position[0]-288/(board_size-1),position[1]-288/(board_size-1)))
                    elif board[i][j]==-1:
                        position=pos([i,j])
                        screen.blit(white_surface,(position[0]-288/(board_size-1),position[1]-288/(board_size-1)))
                    if eval[i][j]==1:
                        position=pos([i,j])
                        pygame.draw.rect(screen,(0,0,0),pygame.Rect(position[0]-144/(board_size-1),position[1]-144/(board_size-1),288/(board_size-1),288/(board_size-1)))
                    elif eval[i][j]==-1:
                        position=pos([i,j])
                        pygame.draw.rect(screen,(255,255,255),pygame.Rect(position[0]-144/(board_size-1),position[1]-144/(board_size-1),288/(board_size-1),288/(board_size-1)))     
            for i in eval:
                stone+=sum(i)
            print('黑领先%s子。'%str(stone-7.5))
        was_pressed=1
    else:
        if was_pressed==1:
            was_pressed=0
            screen.blit(board_surface,(0,0))
            for i in range(board_size):
                for j in range(board_size):
                    if board[i][j]==1:
                        position=pos([i,j])
                        screen.blit(black_surface,(position[0]-288/(board_size-1),position[1]-288/(board_size-1)))
                    elif board[i][j]==-1:
                        position=pos([i,j])
                        screen.blit(white_surface,(position[0]-288/(board_size-1),position[1]-288/(board_size-1)))
            if current_move!=None:
                pygame.draw.circle(screen,(255,0,0),pos(current_move),144/(board_size-1),int(72/(board_size-1)))
        else:        
            if pygame.mouse.get_pressed()[0]:
                mouse_state=2
            else:
                mouse_state=max(mouse_state-1,0)
            if game_mode==1:
                if keyboard.is_pressed('w'):
                    keyboard_state[0]=max(keyboard_state[0]+1,5)
                    mouse_state=0
                else:
                    keyboard_state[0]=0
                if keyboard.is_pressed('s'):
                    keyboard_state[1]=max(keyboard_state[1]+1,5)
                    mouse_state=0
                else:
                    keyboard_state[1]=0
                if keyboard.is_pressed('a'):
                    keyboard_state[2]=max(keyboard_state[2]+1,5)
                    mouse_state=0
                else:
                    keyboard_state[2]=0
                if keyboard.is_pressed('d'):
                    keyboard_state[3]=max(keyboard_state[3]+1,5)
                    mouse_state=0
                else:
                    keyboard_state[3]=0
                moving=0
                if keyboard_state[0] in [1,5]:
                    moving=1
                    if current_move!=None:
                        current_move=(current_move[0],(current_move[1]-1)%board_size)
                    board=up(board)
                    valid=up(valid)
                elif keyboard_state[1] in [1,5]:
                    moving=1
                    if current_move!=None:
                        current_move=(current_move[0],(current_move[1]+1)%board_size)
                    board=down(board)
                    valid=down(valid)
                elif keyboard_state[2] in [1,5]:
                    moving=1
                    if current_move!=None:
                        current_move=((current_move[0]-1)%board_size,current_move[1])
                    board=left(board)
                    valid=left(valid)
                elif keyboard_state[3] in [1,5]:
                    moving=1
                    if current_move!=None:
                        current_move=((current_move[0]+1)%board_size,current_move[1])
                    board=right(board)
                    valid=right(valid)
                if moving==1:
                    board_surface=draw_element()[0]
                    screen.blit(board_surface,(0,0))
                    for i in range(board_size):
                        for j in range(board_size):
                            if board[i][j]==1:
                                position=pos([i,j])
                                screen.blit(black_surface,(position[0]-288/(board_size-1),position[1]-288/(board_size-1)))
                            elif board[i][j]==-1:
                                position=pos([i,j])
                                screen.blit(white_surface,(position[0]-288/(board_size-1),position[1]-288/(board_size-1)))
                    if current_move!=None:
                        pygame.draw.circle(screen,(255,0,0),pos(current_move),144/(board_size-1),int(72/(board_size-1)))
            if mouse_state==1:
                item=get_item()
                if type(item) is not tuple:
                    pass###
                else:
                    if is_valid(item,color_temp):
                        sound.play()
                        for i in death_temp:
                            board[i[0]][i[1]]=0
                        board[item[0]][item[1]]=color_temp
                        current_move=item
                        color_temp*=-1
                        screen.blit(board_surface,(0,0))
                        for i in range(board_size):
                            for j in range(board_size):
                                if board[i][j]==1:
                                    position=pos([i,j])
                                    screen.blit(black_surface,(position[0]-288/(board_size-1),position[1]-288/(board_size-1)))
                                elif board[i][j]==-1:
                                    position=pos([i,j])
                                    screen.blit(white_surface,(position[0]-288/(board_size-1),position[1]-288/(board_size-1)))
                        if current_move!=None:
                            pygame.draw.circle(screen,(255,0,0),pos(current_move),144/(board_size-1),int(72/(board_size-1)))
    pygame.display.flip()
    clock.tick(30)