import numpy as np
import matplotlib.pyplot as plt


def v4_utility(x46,N1):
    return np.log(1+(N1-x46))  # k is the corelation coefficient between SDN and IPv6

def v6_utility(x46,N2):
    return  np.log(1+(N2+x46))

N=16
N1=N/2
N2=N-N1
x46 = np.arange(.0001, N1+0.0001, 1)  # cost sharing factor between SDN and IPv6
plt.subplot(1, 2, 1)
plt.plot(x46, v4_utility(x46, N1), '-or', label='Group-1(initially 15 ISPs)')
plt.plot(x46, v6_utility(x46, N2), '-pg', label='Group-2(initially 15 ISPs)')
plt.xlabel('X4->6')
plt.ylabel('Uk')
plt.legend()
plt.grid(True)

N1=N+4
N2=N-N1
x46 = np.arange(.0001, N1+0.0001, 1)
plt.subplot(1, 2, 2)
plt.plot(x46, v4_utility(x46, N1), '-or', label='Group-1(Initially 20 ISPs)')
plt.plot(x46, v6_utility(x46, N2), '-pg', label='Group-2(Initially 10 ISPs')
plt.xlabel('X4->6')
plt.ylabel('Uk')
plt.legend()
plt.grid(True)
plt.show()
