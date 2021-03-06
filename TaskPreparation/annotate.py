from glob import glob
import random

indir = "trial/"
sysdir = "../Data/system/"
golddir = "../Data/gold/"

cnt=0
goldlines=[]
syslines=[]
for fl in glob('%s*' % indir):
    f=open(fl, 'r')
    goldlines.append('#begin document (%s); ' % fl)
    syslines.append('#begin document (%s); ' % fl)
    for line in f:
        r=random.randint(1, 50000)
        sysfields=line.split('\t')
        sysfields[1]=sysfields[1].strip('\n')
        goldfields=list(sysfields)
        sysfields.append('BODY')
        goldfields.append('BODY')
        if r<=58:
            sysfields.append('(%d)' % r)
            goldfields.append('-')
        elif r<=60:
            sysfields.append('(%d)' % r)
            goldfields.append('(%d)' % r)
        elif r<=62:
            sysfields.append('-')
            goldfields.append('(%d)' % r)
        else:
            goldfields.append('-')
            sysfields.append('-')
        goldlines.append('\t'.join(goldfields))
        syslines.append('\t'.join(sysfields))
    syslines.append("#end document")
    goldlines.append("#end document")
#    cnt+=1
#    if cnt==2:
#        break
with open('%s5.conll' % sysdir, 'w') as w:
    w.write('\n'.join(syslines))
with open('%s5.conll' % golddir, 'w') as w:
    w.write('\n'.join(goldlines))
