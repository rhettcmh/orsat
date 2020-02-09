""" Circular buffer to make ghosting tails for the bodies 
in orbit. Uses numpy to support N bodies each with
a maximum of M points of 3D positional data in a given simulation.
"""

import numpy as np

class GravTails:
    def __init__(self, length, maxlength, n_bodies):
        """ Creates a numpy array with a "pointer" to act
        as a circular buffer for trailing position data.
        This trailing position data is referred to as:
        "Gravtails" 

        :param length: (int) desired length of the buffer.
        :param maxlength: (int) maximum length of the tail allowed
        :param n_bodies: (int) number of bodies in the simulation
        """
        self.buffer = np.zeros((n_bodies, maxlength, 3))
        self.ptr = 0
        self.buffer_curr_size = 0

        self.length = length
        self.maxlength = maxlength
        self.filled_buffer = False

    def _push(self, value):
        """ Puts a value at the "end" of the buffer.
        
        :param value: shape (n_bodies, 3) values to put onto the array 
        """
        self.buffer[:, self.ptr] = value
        self.ptr = (self.ptr + 1) % self.length

        # When the buffer is underfull, grow the tail as items are pushed.
        if not self.filled_buffer:
            if self.length > self.buffer_curr_size:
                self.tail_end = min(self.length, self.buffer_curr_size)
                self.buffer_curr_size += 1
            else:
                self.filled_buffer = True
        else:
            self.tail_end = self.length


    def _resize(self, newlen):
        """ Reduces or increases the size (provided less than)
        the length of the maxlength of the buffer.

        :param newlen: (int) new maximum length of the buffer <= maxlength
        """
        if newlen <= self.maxlength:
            # If we are increasing the length, the buffer won't have enough in it
            # therefore we'll need to fill up the buffer
            if newlen > self.length:
                if self.ptr == 0:
                    self.ptr = self.length 
                self.filled_buffer = False
            elif newlen < self.length:
                if self.ptr >= newlen - 1:
                    self.ptr = 0
            self.length = newlen
        else:
            raise ValueError("newlen should be less than maxlength.")

    def get_tail(self):
        """ Returns the tail of N bodies. """
        tail = np.concatenate(
            (self.buffer[:,self.ptr:self.tail_end],
            self.buffer[:,:self.ptr]),
            axis=1
        )
        return tail

if __name__ == "__main__":
    # Basic testing.
    ddata = np.arange(1, 30).reshape(-1,1)
    ddata = np.repeat(ddata[np.newaxis], 4, axis=0)*np.arange(1, 5).reshape(-1,1,1)
    ddata = np.repeat(ddata, 3, axis=2)

    tracks = GravTails(5, 9, 4)
    for i in range(20):
        tracks._push(ddata[:, i])
        tracks.get_tail()
        if i == 9:
            tracks._resize(8)

        if i == 16:
            tracks._resize(3)
    