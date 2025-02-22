# -*- coding: utf-8 -*-
"""Розрахунок КІН за результатами моделювання МСЕ"""
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

E=2.1e11
G=7.9e10 # модуль зсуву, Па
#G=E/(2+2*nu)
nu=0.28 # коефіцієнт Пуассона
r=0.2/1000 # віддаль від вістря тріщини до місця заміру, м
sigma=56.0e6 # кільцеві напруження, Па ??а з бандажем
d=5.5/1000 # товщина стінки труби, м

def K(V):
    """Коефіцієнт інтенсивності напружень (КІН), Па*м**0.5
    V - половина величини розкриття тріщини, м"""
    k=3-4*nu # для плоского деформування
    #return np.sqrt(2*np.pi)*2*G*V/((1+k)*np.sqrt(r))
    return np.sqrt(2*np.pi/r)*V*E/(4-4*nu**2) # Meinhard Kuna

def K_(s):
    """Коефіцієнт інтенсивності напружень (КІН), Па*м**0.5
    s - напруження біля тріщини, Па"""
    return s*np.sqrt(2*np.pi*r)

def Y(K,a):
    """Поправочна функція"""
    return K/(sigma*np.sqrt(np.pi*a))

def Kt(Y,sigma,a):
    """теоретичне значення КІН, Па*м**0.5
    Y - значення поправочної функції
    sigma - напруження, Па
    a - глибина тріщини, м"""
    return Y*sigma*np.sqrt(np.pi*a)

def Kt1(sigma,b):
    """Теоретичний КІН [Муракамі, т.2, с.556, табл.9.33]
    R - внутрішній радіус труби
    t - товщина стінки труби
    b - глибина тріщини
    a - половина довжини тріщини
    p - внутрішній тиск
    sigma - кільцеві напруження в трубі
    """
    R=62.0/2000
    t=5.5/1000
    Rt=50.0/1000 # радіус кругового фронта тріщини
    a=(Rt**2-(Rt-b)**2)**0.5
    p=sigma*t/R
    Q=1+1.464*(b/a)**1.65
    R0=R+t
    G0=np.interp(b/t, [0.2, 0.5, 0.8], [1.147, 1.584, 2.298])
    G1=np.interp(b/t, [0.2, 0.5, 0.8], [0.685, 0.839, 1.099])
    G2=np.interp(b/t, [0.2, 0.5, 0.8], [0.521, 0.600, 0.739])
    G3=np.interp(b/t, [0.2, 0.5, 0.8], [0.432, 0.480, 0.568])
    Fe=(t/R)*(R*R/(R0*R0-R*R))*(2*G0+2*G1*b/R0+3*G2*(b/R0)**2+4*G3*(b/R0)**3)
    return Fe*(p*R/t)*(np.pi*b/Q)**0.5

def v(K):
    """Швидкість росту тріщини, м/цикл
    K - КІН, Па*м**0.5"""
    K=K/1.0e6 # перевести МПа*м**0.5
    # параметри діаграми втомного руйнування сталі 20Н2М 3% NaCl [моногр. рис. 4.5]:
    C=9.14e-13 # м/(МПа*м**0.5)
    n=3.6
    #C=6.0e-17 # повітря
    #n=6.04
    return C*K**n

a=np.array([0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5])/1000 # глибина тріщини, м

def N(sigma,f,popt):
    """Циклічна довговічність, цикли
    sigma - напруження, Па"""
    a_=np.linspace(a.min(), a.max()) # розміри тріщини, м
    return np.trapz(1/v( Kt(f(a_/d,*popt),sigma,a_) ), a_) # інтеграл по a

def N_(sigma,f,popt): # інший спосіб інтегрування для перевірки
    A=a.min()
    dN=1000.0
    #dA=0.01/1000 # або
    N=0.0
    while A<=a.max():
        K=Kt(f(A/d,*popt),sigma,A)
        V=v(K)
        dA=V*dN
        #dN=dA/V # або
        A=A+dA
        N=N+dN
    return N

def N1(sigma,material):
    """Кількість циклів з рівняння втоми [Трощенко т.1, c.51]"""
    D={"сталь"      :dict(s=210.0e6, N=3.0e6, m=9.00), # середня сталь
       "сталь45"    :dict(s=253.0e6, N=1.8e6, m=8.72), # гладкий зразок, сталь 45, відпал, на повітрі, R=-1 [Трощенко т.1, с.456]
       "сталь45NaCl":dict(s=100.0e6, N=2.5e7, m=2.76), # гладкий зразок, сталь 45, відпал, 3% NaCl, R=-1 [Трощенко т.1, с.456]
       "20Н2М"      :dict(s=190.0e6, N=2.5e6, m=5.86), # моно Рисунок 4.5
       "20Н2МNaCl"  :dict(s=60.00e6, N=2.0e7, m=2.3), # моно Рисунок 4.5
       "20Н2МNaCl_" :dict(s=125.0e6, N=1.0e6, m=1.86), # моно Рисунок 3.15?
       "20Н2М_"     :dict(s=370.0e6, N=1.0e6, m=6.09), # Трощенко с.672
       "20Н2МNaCl__":dict(s=50.0e6, N=5.0e6, m=3.32, m1=10.3) # Трощенко с.672
       }
    d=D[material]
    s=d['s'] # ордината точки перелому кривої втоми в лог. коорд.
    N=d['N'] # абсциса точки перелому кривої втоми в лог. коорд.
    m=d['m'] # показник нахилу кривої втоми в лог. коорд.
    psi=0.2 # коефіцієнт чутливості матеріалу до асиметрії циклу
    s=2*s/(1+psi) # перевід з R=-1 в R=0 (максимальне, а не амплітуда)
    if sigma<s:
        if d.has_key('m1'): return (N*s**d['m1'])/sigma**d['m1'] # якщо крива має 2 переломи
        #else: return 1e8 # включити тільки для візуалізації !
    return (N*s**m)/sigma**m

def S1(n):
    """Напруження з рівняння втоми (обернене до N1 - перевірено) n - кількість циклів"""
    s=253.0e6
    N=1.8e6
    m=8.72
    sigma=((N*s**m)/n)**(1/m) # ампл. напруження для R=-1, що відповідає n
    psi=0.2 # коефіцієнт чутливості матеріалу до асиметрії циклу
    sigma=sigma/(1+psi) # ампл. напруження для R=0, що відповідає n (з залежності sa=sa_eq-psi*sm)
    return 2*sigma # макс. напруження для R=0, що відповідає n

e=a/d # відносна глибина тріщини
# половина величини розкриття тріщини, мкм:
# без бандажу
V1=[0.19311,0.30551,0.40903,0.52202,0.65405,0.79376,0.94576,1.09433,1.24091]
# з бандажем 84 мм
V2=[0.08682, 0.17087, 0.24629, 0.30835, 0.36911, 0.42522, 0.47333, 0.52429, 0.58763]
# з бандажем 74 мм
#V2=[0.09031, 0.17794, 0.25781, 0.32571, 0.39187, 0.4531, 0.50657, 0.55936, 0.62274]
# з бандажем 84 мм no panetration
#V2=[0.18499, 0.29258, 0.39114, 0.49768, 0.62166, 0.75185, 0.89302, 1.03042, 1.16669]
V1=np.array(V1)/1000000 # в метрах
V2=np.array(V2)/1000000

##
Y1=Y(K(V1),a)
def f1(x,a,b,c): # модель
    return a*x**2+b*x+c
popt1, pcov1 = curve_fit(f1, e, Y1) # апроксимувати нелінійним методом найменших квадратів
print popt1 # коефіцієнти a,b,c
print "R^2=", np.corrcoef(Y1, f1(e,*popt1))[0, 1]**2 # коефіцієнт детермінації
print "N(%fПа)="%sigma, np.trapz(1/v(K(V1)), a) # інтегрувати задану масивом функцію методом трапецій

##
Y2=Y(K(V2),a)
def f2(x,a,b,c,d): # модель
    return a*x**3+b*x**2+c*x+d
popt2, pcov2 = curve_fit(f2, e, Y2) # апроксимувати нелінійним методом найменших квадратів
print popt2 # коефіцієнти
print "R^2=", np.corrcoef(Y2, f2(e,*popt2))[0, 1]**2 # коефіцієнт детермінації
print "N(%fПа)="%sigma, np.trapz(1/v(K(V2)),a)

##
plt.figure()
plt.plot(K(V1), v(K(V1))*1e6,'ko-') # кінетична діаграма втомного руйнування
#np.savetxt('KDVRa.csv', v(K(V1))*1e6, delimiter=';')
_=np.loadtxt('KDVRa.csv', delimiter=';')
plt.plot(K(V1), _, 'rs-')
plt.xlabel(u'$K, Пам^{1/2}$'),plt.ylabel(u'$v, мкм/цикл$')
plt.show()

##
plt.figure()
# перевірка - мають збігатись:
plt.plot(a, K(V1), 'ko-')
plt.plot(a, Kt(f1(a/d,*popt1),sigma,a), 'r^-')
plt.plot(a, Kt1(sigma,a), 'rs-')
plt.xlabel('$a$'),plt.ylabel(u'$K$')
plt.show()

##
plt.figure()
S=np.linspace(80.0e6, 500.0e6)
plt.plot([np.log10(N(s,f1,popt1)) for s in S], S, 'k-')
#plt.plot([N(s,f1,popt1) for s in S], S, 'k-')

plt.plot([np.log10(N(s,f2,popt2)) for s in S], S, 'k--')
#plt.plot([N(s,f2,popt2) for s in S], S, 'k--')

# зберегти масиви
#np.savetxt('_.csv', [np.log10(N(s,f2,popt2)) for s in S], delimiter=';')
#нарисувати збережені np.savetxt графіки
_=np.loadtxt('74.csv', delimiter=';')
plt.plot(_, S, 'k:')
_=np.loadtxt('84np.csv', delimiter=';')
plt.plot(_, S, 'r-.')
_=np.loadtxt('73a.csv', delimiter=';')
plt.plot(_, S, 'r-')
_=np.loadtxt('84a.csv', delimiter=';')
plt.plot(_, S, 'r--')

# графіки втоми за рівнянням втоми
import scipy
N1=scipy.vectorize(N1)
S=np.linspace(80.0e6, 500.0e6)
for k,_ in enumerate(["20Н2М","20Н2МNaCl"]):
    plt.plot(np.log10(N1(S,_)), S, 'k-.', linewidth=k+1)

plt.xlabel('$log(N)$'),plt.ylabel(u'$Па$')
plt.grid()
plt.show()

##
plt.figure()
plt.plot(e, Y1, 'ko') # нарисувати еміричну залежність
plt.plot(e, f1(e,*popt1), 'k-') # нарисувати апроксимовану залежність
plt.plot(e, Y2, 'k^')
plt.plot(e, f2(e,*popt2), 'k-')
plt.xlabel('$\epsilon$'),plt.ylabel('$Y$')
plt.show()
