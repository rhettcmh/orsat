import numpy as np

class GravTails:
    """ Circular buffer to make "ghosting" tails for the bodies 
    in orbit. Uses numpy to support N bodies each with
    a maximum of M points of 3D positional data in a given simulation.
    """
    def __init__(self, length, max_length, n_bodies):
        """ Creates a numpy array with "pointers" to act
        as a circular buffer for trailing position data.
        This trailing position data is referred to as
        "Gravtails" 

        :param length: (int) desired length of the buffer.
        :param max_length: (int) maximum length of the tail allowed
        :param n_bodies: (int) number of bodies in the simulation
        """
        # Circular buffer storage.
        self.buffer = np.zeros((n_bodies, max_length, 3))
        self.n_bodies = n_bodies

        # Filling the buffer stats
        self.filled_buffer = False
        self.buffer_curr_size = 0
        self.length = length
        self.max_length = max_length

        # "Pointers" representing a position in the array.
        self.head = 0
        self.tail = -1

    def _push(self, value):
        """ Puts a value at the "end" of the buffer.
        Adjusts the position of the head when the buffer is full.
        
        :param value: shape (n_bodies, 3) values to put onto the array 
        """
        # At every push, data is always inserted at the tail
        self.tail = (self.tail + 1) % self.max_length
        self.buffer[:, self.tail] = value

        if not self.filled_buffer:
            self.buffer_curr_size += 1
            if self.buffer_curr_size == self.max_length:
                self.filled_buffer = True
        
        # Move head when buffer is filled to size length.
        if self.buffer_curr_size >= self.length:
            self.head = (self.head + 1) % self.max_length

    def _resize(self, newlen):
        """ Reduces or increases the size of the "displayed" 
        tail, so long as it does not exceed max_length of the 
        buffer.

        :param newlen: (int) new tail length displayed.
        """
        if newlen <= self.max_length:
            if self.filled_buffer:
                self.head = (self.head - (newlen - self.length)) % self.max_length
            else:
                if newlen > self.buffer_curr_size:
                    if newlen > self.length:
                        self.head = 0
                    elif newlen < self.length:
                        pass
                elif 1 < newlen < self.buffer_curr_size:
                    if newlen > self.length:
                        self.head = max(self.tail - newlen + 1, 0)
                    elif newlen < self.length:
                        self.head += self.length - newlen
            self.length = newlen
        else:
            raise ValueError("The requested length is out of range.")

    def get_tail(self):
        """ Returns the tail of N bodies.
        Head defines the "start" of the trail and 
        tail defines the end (i.e. a[end] -> last 
        element of the tail.
        """
        # Are we in the middle of the vector?
        if self.head < self.tail and self.tail < self.max_length:
            tail = self.buffer[:, self.head:self.tail+1]
        else:
            tail = np.concatenate(
                (self.buffer[:, self.head:],
                self.buffer[:, :self.tail+1]),
                axis=1
            )
        
        # Add a case to handle any 0 centered tracks. 
        # The slider handler if SLAMMED into the side, causes it to get 
        # Values out of range. Either replace slider, or include this case
        # or debug slider functionality. This issue has plagued me for longer 
        # common deceny allows.
        mask = np.any(np.abs(tail) > 1e-3, axis=2)
        tail = tail[mask].reshape(self.n_bodies,-1, 3)

        return tail