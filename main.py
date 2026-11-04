print("ambarawa avocado")
print ("merlin")
import matplotlib.pyplot as plt
bulan = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni']
penjualan = [100, 120, 150, 170, 200, 250]
plt.plot(bulan, penjualan)
plt.xlabel('Bulan')
plt.ylabel('Penjualan')
plt.title('Grafik Penjualan')
plt.show()