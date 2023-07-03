from dataclasses import dataclass

@dataclass
class LevelValues:
    xp: int
    gold: int
    heros: int
    qp: int
    skpt: int
    maxstat: int

LEVEL_VALUES = [
    LevelValues(0,0,0,0,0,0), # Level 0 for proper indexing
    LevelValues(0,0,0,0,1,0),
    LevelValues(100,0,0,0,1,0),
    LevelValues(300,0,0,0,1,0),
    LevelValues(600,0,0,0,1,0),
    LevelValues(1000,0,0,0,1,0),
    LevelValues(2000,0,0,0,1,0),
    LevelValues(4000,0,0,0,1,0),
    LevelValues(8000,0,0,0,1,0),
    LevelValues(14000,0,0,0,1,0),
    LevelValues(20000,0,0,0,2,0), # Level 10
    LevelValues(25000,0,0,0,2,0),
    LevelValues(29000,0,0,0,2,0),
    LevelValues(32000,0,0,0,2,0),
    LevelValues(35000,0,0,0,2,0),
    LevelValues(38000,0,0,0,2,0),
    LevelValues(42000,0,0,0,2,0),
    LevelValues(46000,0,0,0,2,0),
    LevelValues(50000,0,0,0,2,0),
    LevelValues(55000,0,0,0,2,0),
    LevelValues(60000,0,0,0,2,0), # Level 20
    LevelValues(70000,0,0,0,2,0),
    LevelValues(80000,0,0,0,2,0),
    LevelValues(90000,0,0,0,2,0),
    LevelValues(100000,0,0,0,2,0),
    LevelValues(125000,0,0,0,2,0),
    LevelValues(150000,0,0,0,2,0),
    LevelValues(175000,0,0,0,2,0),
    LevelValues(200000,0,0,0,2,0),
    LevelValues(225000,0,0,0,2,0),
    LevelValues(250000,0,0,0,5,0), # Level 30
    LevelValues(300000,0,0,0,2,0),
    LevelValues(350000,0,0,0,2,0),
    LevelValues(400000,0,0,0,2,0),
    LevelValues(450000,0,0,0,2,0),
    LevelValues(500000,0,0,0,2,0),
    LevelValues(600000,0,0,0,2,0),
    LevelValues(700000,0,0,0,2,0),
    LevelValues(800000,0,0,0,2,0),
    LevelValues(900000,0,0,0,2,0),
    LevelValues(1000000,0,0,0,5,0), # Level 40
    LevelValues(1200000,0,0,0,2,0),
    LevelValues(1400000,0,0,0,2,0),
    LevelValues(1700000,0,0,0,2,0),
    LevelValues(2000000,0,0,0,2,0),
    LevelValues(2400000,0,0,0,2,0),
    LevelValues(2800000,0,0,0,2,0),
    LevelValues(3300000,0,0,0,2,0),
    LevelValues(3800000,0,0,0,2,0),
    LevelValues(4400000,0,0,0,2,0),
    LevelValues(5000000,0,0,0,5,1), # Level 50
    LevelValues(6000000,200000,3000,0,1,0),
    LevelValues(8000000,214200,3800,0,1,0),
    LevelValues(10000000,228800,4600,2,1,0),
    LevelValues(12500000,243800,5400,3,1,0),
    LevelValues(15000000,259200,6200,2,1,1),
    LevelValues(20000000,275000,6800,3,1,0),
    LevelValues(25000000,291200,7400,2,1,0),
    LevelValues(30000000,307800,8000,3,1,0),
    LevelValues(35000000,324800,8500,2,1,0),
    LevelValues(40000000,378200,9000,3,4,1), # Level 60
    LevelValues(45000000,433200,9500,2,1,0),
    LevelValues(50000000,489800,10000,3,1,0),
    LevelValues(50000000,548000,10500,2,1,0),
    LevelValues(55000000,607800,11000,3,1,0),
    LevelValues(60000000,669200,11500,2,1,1),
    LevelValues(65000000,732200,12000,3,1,0),
    LevelValues(70000000,796800,12500,2,1,0),
    LevelValues(75000000,863000,13000,3,1,0),
    LevelValues(80000000,930800,13500,2,1,0),
    LevelValues(85000000,1000200,14000,3,4,1), # Level 70
    LevelValues(90000000,1071200,14400,2,1,0),
    LevelValues(95000000,1143800,14800,3,1,0),
    LevelValues(100000000,1218000,15200,2,1,0),
    LevelValues(105000000,1293000,15600,3,1,0),
    LevelValues(110000000,1371200,16000,2,1,1),
    LevelValues(115000000,2441250,16400,3,1,0),
    LevelValues(120000000,2483600,16800,2,1,0),
    LevelValues(125000000,2526650,17200,3,1,0),
    LevelValues(130000000,2570400,17600,2,1,0),
    LevelValues(135000000,2614850,18000,3,4,1), # Level 80
    LevelValues(140000000,2660000,18400,3,1,0),
    LevelValues(145000000,2705850,18800,4,1,0),
    LevelValues(150000000,2752400,19200,3,1,0),
    LevelValues(155000000,2799650,19600,4,1,0),
    LevelValues(160000000,2847600,20000,3,1,1),
    LevelValues(165000000,2896250,20400,4,1,0),
    LevelValues(170000000,2945600,20800,3,1,0),
    LevelValues(180000000,2995650,21200,4,1,0),
    LevelValues(190000000,3046400,21600,3,1,0),
    LevelValues(200000000,3097850,22000,4,4,1), # Level 90
    LevelValues(250000000,3150000,22400,3,1,0),
    LevelValues(300000000,3202850,22800,4,1,0),
    LevelValues(350000000,3256400,23200,3,1,0),
    LevelValues(400000000,3310650,23600,4,1,0),
    LevelValues(500000000,3365600,24000,3,1,1),
    LevelValues(600000000,3421250,24300,4,1,0),
    LevelValues(700000000,3477600,24600,3,1,0),
    LevelValues(800000000,3534650,24900,4,1,0),
    LevelValues(900000000,3592400,25200,3,1,0),
    LevelValues(1000000000,11135092,25555,4,4,3) # Level 100
]