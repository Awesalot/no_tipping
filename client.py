import json
from random import choice
from turtle import right
from hps.clients import SocketClient
from time import sleep
import argparse

HOST = 'localhost'
PORT = 5000

class Node:
    def __init__(self, val = 0) -> None:
        self.data = val
        self.next = None
        self.prev = None
    
class SortedDoubleList:
    def __init__(self) -> None:
        self.head = None
        self.tail = None
        self.len = 0
        
    def addNode(self, val) -> None:
        self.len += 1
        if not self.head: 
            self.head = Node(val)
            self.tail = self.head
            return

        newNode = Node(val)
        self.tail.next = newNode
        newNode.prev = self.tail
        self.tail = newNode
        return

    def getKthMax(self, k):
        curr = self.tail
        for i in range(k):
            curr = curr.prev
        return curr.data

    def delNode(self, val) -> None:
        self.len -= 1
        curr = self.tail
        while curr.data != val:
            curr = curr.prev
        if curr == self.tail: self.tail = curr.prev
        if not curr.prev: 
            self.head = self.head.next
            return
        curr.prev.next = curr.next
        if curr.next: curr.next.prev = curr.prev

    def empty(self):
        if not self.len: return True
        return False
    
    def length(self):
        return self.len

class NoTippingClient(object):
    def __init__(self, name, is_first):
        self.first_resp_recv = False
        self.name = name
        self.client = SocketClient(HOST, PORT)
        self.client.send_data(
            json.dumps({
                'name': self.name,
                'is_first': is_first
            }))
        response = json.loads(self.client.receive_data())
        self.board_length = response['board_length']
        self.num_weights = response['num_weights']

    def play_game(self):
        # pass
        response = {}
        while True:
            response = json.loads(self.client.receive_data())
            if 'game_over' in response and response['game_over'] == "1":
                print("Game Over!")
                exit(0)

            self.board_state = list(
                map(int, response['board_state'].strip().split(' ')))

            if response['move_type'] == 'place':
                position, weight = self.place(self.board_state)
                self.client.send_data(
                    json.dumps({
                        "position": position,
                        "weight": weight
                    }))
            else:
                position = self.remove(self.board_state)
                self.client.send_data(json.dumps({"position": position}))

    def left_torque(self, current_board_state):
        lt = -9
        n = self.board_length
        for i in range(len(current_board_state)):
            if -1 < i < (n - 3):
                lt += (n - i - 3) * current_board_state[i]
            elif (n - 3) < i:
                lt -= (i - n + 3) * current_board_state[i]

        return lt

    def right_torque(self, current_board_state):
        rt = -3
        n = self.board_length
        for i in range(len(current_board_state)):
            if -1 < i < (n - 1):
                rt += (n - i - 1) * current_board_state[i]
            elif (n - 1) < i:
                rt -= (i - n + 1) * current_board_state[i]

        return rt

    def place(self, current_board_state):
        """
        PLACE YOUR PLACING ALGORITHM HERE

        Inputs:
        current_board_state - array of what weight is at a given position on the board

        Output:
        position (Integer), weight (Integer)
        """
        leftTorque = self.left_torque(current_board_state)
        rightTorque = self.right_torque(current_board_state)
        k = -1
        n = self.board_length
        pos = n - 2
        weight = 0
        while True:
            k = k + 1
            if k == weights.length():
                weight = max
                break
            max = weights.getKthMax(k)
            # print(max, leftTorque, leftTorque // max,"max and left")
            leftidx = min(abs(leftTorque) // max, n - 3)
            rightidx = min(rightTorque // max, n + 1)
            if not leftidx and not rightidx: 
                continue
            # print("left, right",leftidx, rightidx)
            # print([(i, x) for i,x in enumerate(current_board_state)])
            if leftidx > rightidx:
                while current_board_state[n - 3 - leftidx] and leftidx > 0:
                    leftidx -= 1
                if leftidx > 0:
                    pos = -leftidx + n - 3
                    weight = max
                    break
            if leftidx <= rightidx:
                while current_board_state[n + rightidx - 1] and rightidx > 0:
                    rightidx -= 1
                if rightidx > 0:
                    pos = n + rightidx - 1
                    weight = max
                    break

            if not current_board_state[n - 1]:
                pos = n - 1
                weight = max
                break
            if not current_board_state[n - 2]:
                # print(current_board_state[n-1], n-1)
                pos = n - 2
                weight = max
                break
            if not current_board_state[n - 3]:
                pos = n - 3
                weight = max
                break
        
        # print("weight:",weight)
        weights.delNode(weight)
        
        return pos - n, weight
    
    def isleaf(self, current_board_state):
        if self.left_torque(current_board_state) < 0 or self.right_torque(current_board_state) < 0:
            return True
        else: return False

    def test(self,  current_board_state, depth):
        if not depth or self.isleaf(current_board_state):
            if self.left_torque(current_board_state) >= 0 and self.right_torque(current_board_state) >= 0:
                return True, -1
            else: return False, -1
        temp = 0
        if depth % 2 == 1:
            for i in range(len(current_board_state)):
                if not current_board_state[i]:
                    temp, current_board_state[i] = current_board_state[i], temp
                    check, _ = self.test(self, current_board_state, depth - 1)
                    temp, current_board_state[i] = current_board_state[i], temp
                    if check: return True, i
            return False, -1
        else:
            for i in range(len(current_board_state)):
                if not current_board_state[i]:
                    temp, current_board_state[i] = current_board_state[i], temp
                    check = self.test(self, current_board_state, depth - 1)
                    temp, current_board_state[i] = current_board_state[i], temp
                    if not check: return True, i
            return False, -1

    def closest(self, current_board_state):
        n = self.board_length * 2
        mid = n // 2
        left = 0
        right = n - 1

        if current_board_state[mid - 2]:
            return mid - 2
        
        for i in range(mid - 1, n):
            if not current_board_state[i]:
                right = i
                break
        for i in range(0, mid - 2):
            if not current_board_state[i]:
                left = i
                break
        
        return min(left, right)

    def remove(self, current_board_state):
        """
        PLACE YOUR REMOVING ALGORITHM HERE

        Inputs:
        current_board_state - array of what weight is at a given position on the board

        Output:
        position (Integer)
        """
        n = self.board_length
        check, pos = self.test(current_board_state, 10) 
        if check: return (pos - n)
        else:
            return (self.closest(current_board_state) - n)

weights = SortedDoubleList()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--first',
                        action='store_true',
                        default=False,
                        help='Indicates whether client should go first')
    parser.add_argument('--ip', type=str, default='localhost')
    parser.add_argument('--port', type=int, default=5000)
    parser.add_argument('--name', type=str, default="Python Demo Client")
    args = parser.parse_args()

    HOST = args.ip
    PORT = args.port

    player = NoTippingClient(args.name, args.first)
    
    for i in range(player.num_weights):
        weights.addNode(i + 1)

    player.play_game()
