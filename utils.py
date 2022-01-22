import numpy as np
import cv2
import copy
import json
import random
from shapely.geometry import Polygon

# Task 1.1
def visualization(image_path,data_path,opacity):
    '''
    Input: This function takes in the path of the image, the json data path and opacity
    Output: The output is a list of 2 images first one with shading on damage areas, second one with BBox around car parts with their names.
    '''
    font = cv2.FONT_HERSHEY_SIMPLEX
    color,max_min,text = [],[],[]
    img = cv2.imread(image_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_copy = copy.deepcopy(img)
    
    with open(data_path) as f:
        data = json.load(f)

    try:
        width = data[1]['original_width']
        height = data[1]['original_height']
    except:
        print('There was problem in acquiring the width and height of the image')

    for y in range(len(data)):
        a,b,c = random.randint(0,255),random.randint(0,255),random.randint(0,255)
        color.append((a,b,c))
        try:
            ls = data[y]['value']['points']
        except:
            continue
        
        for x in ls:
            x[0] = (x[0]*width)/100
            x[1] = (x[1]*height)/100
        
        # drawing the polygons 
        pts1 = np.array(ls,dtype=np.int32).reshape((-1,1,2))
        img = cv2.polylines(img,[pts1],
                            isClosed=True,
                            color=(a/4,b/4,c/4),
                            thickness=3)

        
        # for the color inside the polygons
        cv2.fillPoly(img, [pts1], (a,b,c))
          
    img = cv2.addWeighted(img, opacity, img_copy, (1-opacity), 0.0) 
    img1 = copy.deepcopy(img)
    for y in range(len(data)):
        try:
            ls = data[y]['value']['points']
        except:
            continue
            
        # for bbox
        for i,j in enumerate(ls):
            if i == 0:
                xmin,ymin,xmax,ymax  = j[0],j[1],j[0],j[1]
            else:
                if j[0]<xmin:
                    xmin = j[0]
                if j[0]>xmax:
                    xmax = j[0]
                if j[1]< ymin:
                    ymin = j[1]
                if j[1] > ymax:
                    ymax = j[1]
                    
        max_min.append([xmin,ymin])
            
        cv2.rectangle(img,
              pt1=(int(xmin),int(ymin)),
              pt2=(int(xmax),int(ymax)),
              color=color[y],
             thickness=2)
        
        text.append(data[y]['value']['polygonlabels'][0])
        
    for x,y in enumerate(text): 
        # for the text in the bbox
        cv2.putText(img, text = y,
                   org=(int(max_min[x][0])+5,int(max_min[x][1])+15),
                   fontFace=font,
                   fontScale=0.4,
                   color=(255,255,255),
                   thickness=1,
                   lineType=cv2.LINE_AA)
             
    return [img1,img]


# Task 1.2
def damages(damage_path,parts_path):
    '''
    Input: This function takes the json data about damage and parts information
    Output: The output is in the form of a list of parts which are damaged, what the damage is and what percentage of the car part is damaged
    '''
    parts_list,damages_list = [],[]
    damage_percent = []
    damaged_part_name = []
    damage_names_list = []
    
    # accessing the data files
    with open(parts_path) as f:
        parts = json.load(f)
    with open(damage_path) as f1:
        damages = json.load(f1)

    width = parts[0]['original_width']
    height = parts[0]['original_height']
    
    # normalization of dimensions
    for part in parts:
        part_polygon = part['value']['points']
        for x in part_polygon:
            x[0] = int((x[0]*width)/100)
            x[1] = int((x[1]*height)/100)
        parts_list.append(part_polygon)
    for damage in damages:
        damaged_part_polygon = damage['value']['points']
        for y in damaged_part_polygon:
            y[0] = int((y[0]*width)/100)
            y[1] = int((y[1]*height)/100)
        damages_list.append(damaged_part_polygon)
        
    # to iterate through all the parts and find out which parts have damage, what is the type of
    # damage and the damage percentage
    for m,part2 in enumerate(parts_list):
        part_area = cv2.contourArea(np.around([pt for pt in part2]))
        damage_area = []
        damage_name = []
        
        for damage2 in damages_list:
            p1 = Polygon(part2)
            p2 = Polygon(damage2)
            # if the polygon of part and damage intersect then we move on to note that down
            # and calculate the damage percentage
            if p1.intersects(p2):
                damage_name.append(damage['value']['polygonlabels'][0])
             
                mask = np.zeros((height,width), dtype=np.uint8)
                mask1 = np.zeros((height,width), dtype=np.uint8)
                points = np.around([[pt] for pt in damage2]).reshape(1,len(damage2),2)
                points2 = np.around([[pt] for pt in part2]).reshape(1,len(part2),2)

                cv2.fillPoly(mask, points, (255,255,255))
                cv2.fillPoly(mask1, points2, (255,255,255))
                dst = cv2.addWeighted(mask, 0.5, mask1, 0.5, 0.0)

                for x in range(dst.shape[0]):
                    for y in range(dst.shape[1]):
                        if dst[x][y] != 255:
                            dst[x][y] = 0

                c, _ = cv2.findContours(dst, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
                                
                # calculating the percent damage
                damage_area.append(cv2.contourArea(np.around([pt for pt in c[0]])))
                
        total_affected_area = sum(damage_area)*100/part_area
        if len(damage_area)>0 and total_affected_area>1.5:
            damage_percent.append(total_affected_area)
            damaged_part_name.append(parts[m]['value']['polygonlabels'][0])
            damage_names_list.append(damage_name)
    
    # for the final output string part
    d = dict()
    para=[]
    for name in damage_names_list:
        d = dict()
        for x in name:
            if x not in d.keys():
                d[x]=1
            else:
                d[x]+=1

        temp = []
        count = 1
        for x,y in d.items():
            if len(d)>1 and count<len(d):
                temp.extend([str(y),x,','])
                count +=1
            else:
                temp.extend([str(y),x])

        para.append(' '.join(temp))
        
    output = []
    for l in range(len(damage_percent)):
        output.append(f'found {para[l]} on {damaged_part_name[l]} with {round(damage_percent[l],2)}% damage.')
    
    return output