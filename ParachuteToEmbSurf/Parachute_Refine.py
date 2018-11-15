#################################
# StructureFile
# fixed displacement point
# fixed rotation point
#
# mesh_Structural.top.quad
# NODES
#
#
# mesh_Structural.surfacetop.quad
#################################
import sys
import numpy as np
from scipy.optimize import fsolve
import Catenary

class Elem:
    def __init__(self, id, nodes, att = 0, eframe = None):
        self.id = id
        self.nodes = nodes
        self.att = att
        self.eframe = eframe

def RepresentsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def ReadNodes(file):
    line = file.readline()  # should be "Nodes FluidNodes"
    while line:
        data = line.split()
        if data[0] == 'NODES' or data[0] == 'Nodes':
            break
        line = file.readline()
    print('ReadNodes, the first line is ', line)
    nodes = []
    while line:
        line = file.readline()
        data = line.split()
        if data[0][0] == '*' or data[0] == 'NODES' or data[0] == 'Nodes':
            continue
        if RepresentsInt(data[0]):
            nodes.append(list(map(float, data[1:4])))
        else:
            break

    print("ReadNodes reads ", len(nodes), " nodes")
    return file, line, nodes
def pair(a,b):
    return (min(a,b), max(a,b))

def ReadElems(file, line):
    print('\n\n*ReadElems, the first line is ', line)
    elems = []
    type = -1
    name = line.split()[1]
    while line:
        line = file.readline()
        data = line.split()
        if not line or data[0][0] == '*':
            continue
        if RepresentsInt(data[0]):
            type = len(data) - 2
            elems.append(Elem(int(data[0]), list(map(int, data[2:]))))

        else:
            break
    if line.split()[0]  == 'ATTRIBUTES':
        ind = 0
        while line:
            line = file.readline()
            data = line.split()
            if not line or data[0][0] == '*':
                continue
            if RepresentsInt(data[0]):
                elems[ind].att = int(data[1])
                assert(elems[ind].id == int(data[0]))
                ind += 1

            else:
                break
    if line.split()[0]  == 'EFRAMES':
        ind = 0
        while line:
            line = file.readline()
            data = line.split()
            if not line or data[0][0] == '*':
                continue
            if RepresentsInt(data[0]):
                elems[ind].eframe = list(map(float, data[1:]))
                assert(elems[ind].id == int(data[0]))
                ind += 1

            else:
                break
    print('ReadElems reads ', len(elems), ' ', name, ' elems')
    return file, line, elems, type, name


def line_to_circle(theta, data):
    a = data[0]
    return a*theta - 2 * np.sin(theta/2.)

def SplitLines(line_elems):
    '''
    :param line_elems:
    :return:
    '''
    j_old = -1
    line, lines = [], []
    for i_e in range(len(line_elems)):
        i,j = line_elems[i_e].nodes
        if i != j_old:
            if line:
                lines.append(line)
            line = [i,j]

        else:
            line.append(j)
        j_old = j
    lines.append(line)
    return lines

class Mesh:
    '''
    #  nodes set
    #  topology set
    '''
    def __init__(self):
        self.nodes = None
        self.ele_set = []
        self.ele_set_info = []

    def read_stru(self, file_name):
        '''
        :param inputStru:
        :param beamPars: parameters to handle phantom surface, skip beamPars[0] beams at all ends of these lines, the shape of
        the cross section beamPars[1], 4 for square, radius of the cross section beamPars[2]
        :return: nodes: a list of 3 double,
                 elems: a list of 3 int
        '''

        try:
            stru_file = open(file_name, "r")
        except IOError:
            print("File '%s' not found." % file_name)
            sys.exit()


        print('Reading Structure mesh ...')
        file, line, self.nodes = ReadNodes(stru_file)
        while line:
            '''
            It should read (0)Band Gores, Disk Gores, (1)Gap Lines, (2)Suspension Lines, (3)Vent Lines
            '''
            stru_file, line, elems, type, name = ReadElems(stru_file, line)
            self.ele_set.append(elems)
            self.ele_set_info.append([name, type])
        stru_file.close()

    def refine(self, refine_all_beams_or_not = True):
        '''
        add nodes, append to nodes
        change quad
        change beams in quad
        change other beams
        :return:
        '''


        nodes = self.nodes
        ele_set = self.ele_set
        ele_set_info = self.ele_set_info

        n_n = len(nodes) # save number of nodes
        n_es = len(ele_set)

        edge_to_center_node = {}
        new_ele_set = []

        ################   Update canopy
        for i_es in range(n_es):
            ele = ele_set[i_es]
            ele_info = ele_set_info[i_es]
            new_ele = []
            if ele_info[1] == 2:
                print('beam')
                #beam
            elif ele_info[1] == 4:
                print('quad')
                n_e = len(ele)
                for i_e in range(n_e):
                    id = ele[i_e].id
                    att = ele[i_e].att
                    eframe = ele[i_e].eframe
                    ele_nodes = ele[i_e].nodes
                    new_nodes = [0,0,0,0,0]
                    # step 1: add a new node at the center
                    new_nodes[0] = n_n + 1
                    n_n += 1

                    # update node coordinate
                    # todo
                    new_node_coord = [(nodes[ele_nodes[0] - 1][0] + nodes[ele_nodes[1] - 1][0] + nodes[ele_nodes[2] - 1][0] + nodes[ele_nodes[3] - 1][0]) / 4.0,
                                      (nodes[ele_nodes[0] - 1][1] + nodes[ele_nodes[1] - 1][1] + nodes[ele_nodes[2] - 1][1] + nodes[ele_nodes[3] - 1][1]) / 4.0,
                                      (nodes[ele_nodes[0] - 1][2] + nodes[ele_nodes[1] - 1][2] + nodes[ele_nodes[2] - 1][2] + nodes[ele_nodes[3] - 1][2]) / 4.0]

                    nodes.append(new_node_coord)

                    for i_n in range(ele_info[1]):
                        if pair(ele_nodes[i_n - 1], ele_nodes[i_n]) in edge_to_center_node:
                            #the node is exists
                            new_nodes[i_n + 1] = edge_to_center_node[pair(ele_nodes[i_n - 1], ele_nodes[i_n])]
                        else:
                            new_nodes[i_n + 1] = n_n + 1
                            # update map
                            edge_to_center_node[pair(ele_nodes[i_n - 1], ele_nodes[i_n])] = n_n + 1
                            # update node coordinate
                            #todo
                            new_node_coord = [(nodes[ele_nodes[i_n - 1] - 1][0] + nodes[ele_nodes[i_n] - 1][0]) / 2.0,
                                              (nodes[ele_nodes[i_n - 1] - 1][1] + nodes[ele_nodes[i_n] - 1][1]) / 2.0,
                                              (nodes[ele_nodes[i_n - 1] - 1][2] + nodes[ele_nodes[i_n] - 1][2]) / 2.0]

                            nodes.append(new_node_coord)

                            n_n += 1

                    new_ele.append(Elem(id, [ele_nodes[0], new_nodes[2], new_nodes[0], new_nodes[1]], att, eframe))
                    new_ele.append(Elem(id, [ele_nodes[1], new_nodes[3], new_nodes[0], new_nodes[2]], att, eframe))
                    new_ele.append(Elem(id, [ele_nodes[2], new_nodes[4], new_nodes[0], new_nodes[3]], att, eframe))
                    new_ele.append(Elem(id, [ele_nodes[3], new_nodes[1], new_nodes[0], new_nodes[4]], att, eframe))

            new_ele_set.append(new_ele)

        ################Update beams on the canopy
        for i_es in range(n_es):
            ele = ele_set[i_es]
            ele_info = ele_set_info[i_es]
            new_ele = new_ele_set[i_es]
            if ele_info[1] == 2:
                # beam
                n_e = len(ele)
                for i_e in range(n_e):
                    id = ele[i_e].id
                    att = ele[i_e].att
                    eframe = ele[i_e].eframe
                    ele_nodes = ele[i_e].nodes

                    if pair(ele_nodes[0], ele_nodes[1]) in edge_to_center_node:
                        # the node is exists
                        new_nodes = edge_to_center_node[pair(ele_nodes[0], ele_nodes[1])]
                        # update element
                        # todo attributes and eframe
                        new_ele.append(Elem(id, [ele_nodes[0], new_nodes], att, eframe))
                        new_ele.append(Elem(id, [new_nodes, ele_nodes[1]], att, eframe))


        ################Update beams not on the canopy

        for i_es in range(n_es):
            ele = ele_set[i_es]
            ele_info = ele_set_info[i_es]
            new_ele = new_ele_set[i_es]
            if ele_info[1] == 2:
                # beam
                n_e = len(ele)
                for i_e in range(n_e):
                    id = ele[i_e].id
                    att = ele[i_e].att
                    eframe = ele[i_e].eframe
                    ele_nodes = ele[i_e].nodes

                    if pair(ele_nodes[0], ele_nodes[1]) in edge_to_center_node:
                        # the node is exists
                        continue
                    else:
                        if refine_all_beams_or_not:
                            new_nodes = n_n + 1
                            # update map
                            edge_to_center_node[pair(ele_nodes[0], ele_nodes[1])] = n_n + 1
                            # update node coordinate
                            # todo
                            new_node_coord = [(nodes[ele_nodes[0] - 1][0] + nodes[ele_nodes[1] - 1][0])/2.0,
                                              (nodes[ele_nodes[0] - 1][1] + nodes[ele_nodes[1] - 1][1])/2.0,
                                              (nodes[ele_nodes[0] - 1][2] + nodes[ele_nodes[1] - 1][2])/2.0]
                            nodes.append(new_node_coord)
                            n_n += 1

                            new_ele.append(Elem(id, [ele_nodes[0], new_nodes], att, eframe))
                            new_ele.append(Elem(id, [new_nodes, ele_nodes[1]], att, eframe))
                        else :# do not refine these beams
                            new_ele.append(Elem(id, [ele_nodes[0], ele_nodes[1]], att, eframe))


        self.ele_set = new_ele_set

    def write_stru(self, stru_file_name, surf_file_name, thickness = 2.e-3):
        print('Writing mesh ...')
        stru_file = open(stru_file_name, 'w')
        surf_file = open(surf_file_name, 'w')
        stru_file.write('NODES\n')

        # Step1.1 write nodes
        nodes = self.nodes
        n_n = len(nodes)
        for i in range(n_n):
            stru_file.write('%d  %.16E  %.16E  %.16E\n' % (
            i + 1, nodes[i][0], nodes[i][1], nodes[i][2]))

        # Step1.2 write TOPOLOGY
        ele_set = self.ele_set
        ele_set_info = self.ele_set_info
        n_es = len(ele_set)
        stru_ele_start_id = 1
        surf_ele_start_id = 1
        for i in range(n_es):
            ele_new = ele_set[i]
            ele_info = ele_set_info[i]
            stru_file.write('*  %s\n' % ele_info[0])
            stru_file.write('TOPOLOGY\n')
            n_e = len(ele_new)
            type = fem_type = ele_info[1]
            if type == 2:
                fem_type = 6
            elif type == 4:
                fem_type = 16

            for j in range(n_e):
                if (type == 2):
                    stru_file.write('%d  %d  %d  %d\n' % (stru_ele_start_id + j, fem_type, ele_new[j].nodes[0], ele_new[j].nodes[1]))
                if (type == 4):
                    stru_file.write(
                        '%d  %d  %d  %d  %d  %d\n' % (stru_ele_start_id + j, fem_type, ele_new[j].nodes[0], ele_new[j].nodes[1], ele_new[j].nodes[2], ele_new[j].nodes[3]))
            stru_file.write('ATTRIBUTES\n')
            for j in range(n_e):
                stru_file.write('%d  %d\n' % (stru_ele_start_id + j, ele_new[j].att))

            if(type == 2): #beam elements need EFRAMES
                stru_file.write('EFRAMES\n')
                for j in range(n_e):
                    stru_file.write('%d  %.16E  %.16E  %.16E  %.16E  %.16E  %.16E  %.16E  %.16E  %.16E\n' % (stru_ele_start_id + j,
                                                                                                             ele_new[j].eframe[0], ele_new[j].eframe[1], ele_new[j].eframe[2],
                                                                                                             ele_new[j].eframe[3], ele_new[j].eframe[4], ele_new[j].eframe[5],
                                                                                                             ele_new[j].eframe[6], ele_new[j].eframe[7], ele_new[j].eframe[8]))

            stru_ele_start_id += n_e
            ############Write Sufrace top
            if (type == 4):
                name = ele_info[0]
                surf_id = 1 if name == 'Disk_Gores' else 2
                surf_file.write('SURFACETOPO %d SURFACE_THICKNESS %.16E\n' %(surf_id, thickness))

                for j in range(n_e):
                    surf_file.write(
                        '%d  %d  %d  %d  %d  %d\n' % (
                         j + surf_ele_start_id, 1, ele_new[j].nodes[0], ele_new[j].nodes[1], ele_new[j].nodes[2], ele_new[j].nodes[3]))
                surf_ele_start_id += n_e

        stru_file.close()
        surf_file.close()

    def visualize_disp(self):
        '''
        update node coordinate to include the displacement
        :return:
        '''
        nodes = self.nodes
        node_disp = self.node_disp
        nn = len(nodes)
        for i_n in range(nn):
            nodes[i_n] = nodes[i_n][0] + node_disp[i_n][0], nodes[i_n][1] + node_disp[i_n][1], nodes[i_n][2] + node_disp[i_n][2]

    def folding(self, n):
        '''
        First fold the Disk, then the band, and the suspension lines
        n : number of
        :return: disp

        '''
        nodes = self.nodes
        ele_set = self.ele_set
        ele_set_info = self.ele_set_info
        node_disp = np.zeros([len(nodes),3])
        #parachute parameters
        r_d, R_d, h_d =  0.788, 7.7235, 39.2198 #Disk inner radius, outer radius and z
        R_b, ht_b, hb_b = 7.804, 38.3158, 35.7358 #Band radius, band top z and band bottom z
        h0 = 0
        L_s, L_v, L_g = np.sqrt(R_b**2 + hb_b**2), r_d/2., np.sqrt((R_d - R_b)**2 + (h_d - ht_b)**2) # Suspension_Lines length ,  Vent_Lines length,    Gap_Lines length

        # todo the second parameter is the z displacement of band
        band_b3 = 0.0

        # todo the second parameter is the z displacement of disk
        disk_b3 = 50.0

        band_deform_method = 'rigid'

        line_relax_method = 'catenary'

        ############ piece map
        theta = np.pi / n

        ################################################ This is for the disk
        # todo the first parameter is cosa in [0, 1]
        cosa = 0.5
        sina = -np.sqrt(1 - cosa * cosa)
        # todo check can also be + sina / np.cos(theta)
        cosb = (sina * cosa * np.tan(theta) - sina / np.cos(theta)) / (1 + sina * sina * np.tan(theta) * np.tan(theta))
        sinb = -cosa + cosb * sina * np.tan(theta)
        print('cosb^2 + sinb^2 = ', cosb * cosb + sinb * sinb)

        disk_rot0 = np.array([[cosa, -cosb * sina, -sinb * sina],
                         [0, cosa - cosb * sina * np.tan(theta), cosb],
                         [sina, cosb * cosa, sinb * cosa]])

        disk_disp = np.array([0, 0, disk_b3])
        print('orthogonal matrix test ', np.dot(disk_rot0.T, disk_rot0))

        # The rigid motion of the first half gore is rot0*x + disp0
        x1 = np.array([r_d, 0, 0])
        x2 = np.array([R_d, 0, 0])
        x3 = np.array([r_d*np.cos(theta), r_d*np.sin(theta), 0])
        x4 = np.array([R_d*np.cos(theta), R_d*np.sin(theta), 0])

        y1 = np.dot(disk_rot0, x1) + disk_disp
        print('y1 is ', y1)
        y2 = np.dot(disk_rot0, x2) + disk_disp
        print('y1 is ', y2)
        y3 = np.dot(disk_rot0, x3) + disk_disp
        print('y1 is ', y3)
        y4 = np.dot(disk_rot0, x4) + disk_disp
        print('y1 is ', y4)

        disk_rot_matrices = []

        ######################
        for gore_id in range(n):
            #Handle the piece of theta = [2pi/n * gore_id, 2pi/n * (gore_id+1)]
            #The piece will be fold at the center

            ##
            # The the map is
            # rotn = R_z(theta*n) * rot0 * R_z(theta*n)^{-1}
            # bi = b0
            ##
            R_z = np.array([[np.cos(2*gore_id*theta), -np.sin(2*gore_id*theta), 0.],
                            [np.sin(2*gore_id*theta), np.cos(2*gore_id*theta), 0.],
                            [0.,0.,1.]])
            disk_rotn = np.dot(R_z, np.dot(disk_rot0, R_z.T))

            Ref_z = np.array([[np.cos((4*gore_id+2)*theta), np.sin((4*gore_id+2)*theta), 0.],
                              [np.sin((4*gore_id+2)*theta), -np.cos((4*gore_id+2)*theta), 0.],
                              [0., 0., 1.]])
            disk_rotn_2 = np.dot(Ref_z, np.dot(disk_rotn, Ref_z.T))
            disk_rot_matrices.append(disk_rotn)
            disk_rot_matrices.append(disk_rotn_2)

        ################################################ This is for the band, there are two maps,
        # 1) flat
        # 2) rigid
        # todo the first parameter is r_b_deform in [0, R_b]
        r_b_deform = 5.0

        if band_deform_method == 'rigid':
            l_b_deform = 2*R_b*np.sin(theta/2.)
            R_b_deform = r_b_deform * np.cos(theta) - np.sqrt(l_b_deform*l_b_deform - r_b_deform*r_b_deform*np.sin(theta)*np.sin(theta))
            # todo check can also be - np.sqrt
            cosa = (r_b_deform*np.sin(theta)*np.sin(theta) - np.sqrt(r_b_deform**2 * np.sin(theta)**4 - 2.*(1 - np.cos(theta))*(r_b_deform**2 * np.sin(theta)**2 - R_b**2*(1 - np.cos(theta))**2)))\
                   /(2*R_b*(1. - np.cos(theta)))
            sina = -np.sqrt(1 - cosa * cosa)
            print('cosa and sin a : ', cosa, ' ', sina)
            band_rot0 = np.array([[cosa, -sina, 0],
                                  [sina,  cosa, 0],
                                  [   0,     0, 1]])
            band_disp0 = np.array([R_b_deform, 0, 0]) - np.dot(band_rot0, np.array([R_b, 0, 0]))

            band_disp0[2] += band_b3

            ##todo start debug validation
            band_disp0_ = np.array([r_b_deform*np.cos(theta), r_b_deform*np.sin(theta), 0]) - np.dot(band_rot0, np.array([R_b*np.cos(theta), R_b*np.sin(theta), 0]))
            band_disp0_[2] += band_b3
            assert(np.linalg.norm(band_disp0 - band_disp0_) < 1e-10)
            ##todo end debug validation


            band_rot_matrices = []
            band_disp_vectors = []

            ######################
            for gore_id in range(n):
                # Handle the piece of theta = [2pi/n * gore_id, 2pi/n * (gore_id+1)]
                # The piece will be fold at the center

                ##
                # The the map is
                # rotn = R_z(theta*n) * rot0 * R_z(theta*n)^{-1}
                # bi = b0
                ##
                R_z = np.array([[np.cos(2 * gore_id * theta), -np.sin(2 * gore_id * theta), 0.],
                                [np.sin(2 * gore_id * theta), np.cos(2 * gore_id * theta), 0.],
                                [0., 0., 1.]])
                band_rotn = np.dot(R_z, np.dot(band_rot0, R_z.T))
                band_dispn = np.dot(R_z, band_disp0)

                Ref_z = np.array([[np.cos((4 * gore_id + 2) * theta), np.sin((4 * gore_id + 2) * theta), 0.],
                                  [np.sin((4 * gore_id + 2) * theta), -np.cos((4 * gore_id + 2) * theta), 0.],
                                  [0., 0., 1.]])
                band_rotn_2 = np.dot(Ref_z, np.dot(band_rotn, Ref_z.T))
                band_dispn_2 = np.dot(Ref_z, band_dispn)
                band_rot_matrices.append(band_rotn)
                band_rot_matrices.append(band_rotn_2)
                band_disp_vectors.append(band_dispn)
                band_disp_vectors.append(band_dispn_2)


        n_n = len(nodes)  # save number of nodes
        n_es = len(ele_set)

        ################   Update canopy
        for i_es in range(n_es):
            ele = ele_set[i_es]
            ele_info = ele_set_info[i_es]
            if ele_info[1] == 4 and ele_info[0] == 'Disk_Gores':
                n_e = len(ele)
                for i_e in range(n_e):
                    ele_nodes = ele[i_e].nodes
                    for i_n in ele_nodes:
                        xx = nodes[i_n - 1]
                        angle_x = np.arctan2(xx[1], xx[0])   #[-pi, 2pi]
                        gore_id = int((angle_x + 2 * np.pi)/theta)%(2*n)
                        # For the piece  [pi/n * gore_id, pi/n * (gore_id + 1)]
                        # map the point xx -> rot_A * (xx - c) + c + disp_b, here c = [0, 0, xx[2]]


                        disk_rot = disk_rot_matrices[gore_id]
                        xx_shift, disp_shift = np.array([xx[0], xx[1], 0.0]), np.array([0, 0, xx[2]])
                        new_xx = np.dot(disk_rot, xx_shift) + disk_disp + disp_shift

                        node_disp[i_n - 1,:] =  new_xx[0] - xx[0], new_xx[1] - xx[1], new_xx[2] - xx[2]

            if ele_info[1] == 4 and ele_info[0] == 'Band_Gores':
                n_e = len(ele)
                if band_deform_method == 'rigid':
                    for i_e in range(n_e):
                        ele_nodes = ele[i_e].nodes
                        for i_n in ele_nodes:
                            xx = nodes[i_n - 1]
                            angle_x = np.arctan2(xx[1], xx[0])  # [-pi, pi]
                            gore_id = int((angle_x + 2 * np.pi) / theta) % (2 * n)
                            # For the piece  [pi/n * gore_id, pi/n * (gore_id + 1)]
                            # map the point xx -> rot_A * xx  + disp

                            band_rot = band_rot_matrices[gore_id]
                            band_disp = band_disp_vectors[gore_id]
                            new_xx = np.dot(band_rot, xx) + band_disp

                            node_disp[i_n - 1, :] = new_xx[0] - xx[0], new_xx[1] - xx[1], new_xx[2] - xx[2]
                elif band_deform_method == 'flat':

                    l_b_deform = theta * R_b
                    R_b_deform = r_b_deform * np.cos(theta) - np.sqrt(
                        l_b_deform * l_b_deform - r_b_deform * r_b_deform * np.sin(theta) * np.sin(theta))

                    for i_e in range(n_e):
                        ele_nodes = ele[i_e].nodes
                        for i_n in ele_nodes:
                            xx = nodes[i_n - 1]
                            angle_x = np.arctan2(xx[1], xx[0])   # [-pi, pi]
                            gore_id = int((angle_x + 2 * np.pi)/ theta) % (2 * n)
                            # For the piece  [pi/n * gore_id, pi/n * (gore_id + 1)]
                            # map the point xx -> rot_A * xx  + disp

                            d_theta = angle_x - gore_id*theta if angle_x >= 0 else angle_x + 2*np.pi - gore_id*theta
                            assert(d_theta <=  theta and d_theta >= 0)
                            ds = d_theta * R_b

                            start_deform = np.empty(3)
                            end_deform = np.empty(3)
                            if gore_id % 2 == 0:
                                start_deform[:] = R_b_deform*np.cos(gore_id*theta), R_b_deform*np.sin(gore_id*theta), 0
                                end_deform[:]   = r_b_deform*np.cos((gore_id+1)*theta), r_b_deform*np.sin((gore_id+1)*theta), 0
                            else: #gore_id%2 == 1
                                start_deform[:] = r_b_deform * np.cos(gore_id*theta), r_b_deform * np.sin(gore_id*theta), 0
                                end_deform[:] = R_b_deform * np.cos((gore_id+1)*theta), R_b_deform * np.sin((gore_id+1)*theta), 0


                            new_xx = (1 - ds/l_b_deform)*start_deform + ds/l_b_deform*end_deform
                            new_xx[2] = xx[2] + band_b3

                            node_disp[i_n - 1, :] = new_xx[0] - xx[0], new_xx[1] - xx[1], new_xx[2] - xx[2]

        n_n = len(nodes)  # save number of nodes
        n_es = len(ele_set)

        ################   Update canopy
        for i_es in range(n_es):
            ele = ele_set[i_es]
            ele_info = ele_set_info[i_es]
            if ele_info[1] == 4 and ele_info[0] == 'Disk_Gores':
                n_e = len(ele)
                for i_e in range(n_e):
                    ele_nodes = ele[i_e].nodes
                    for i_n in ele_nodes:
                        xx = nodes[i_n - 1]
                        angle_x = np.arctan2(xx[1], xx[0])  # [-pi, 2pi]
                        gore_id = int((angle_x + 2 * np.pi) / theta) % (2 * n)
                        # For the piece  [pi/n * gore_id, pi/n * (gore_id + 1)]
                        # map the point xx -> rot_A * (xx - c) + c + disp_b, here c = [0, 0, xx[2]]


                        disk_rot = disk_rot_matrices[gore_id]
                        xx_shift, disp_shift = np.array([xx[0], xx[1], 0.0]), np.array([0, 0, xx[2]])
                        new_xx = np.dot(disk_rot, xx_shift) + disk_disp + disp_shift

                        node_disp[i_n - 1, :] = new_xx[0] - xx[0], new_xx[1] - xx[1], new_xx[2] - xx[2]

            if ele_info[1] == 4 and ele_info[0] == 'Band_Gores':
                n_e = len(ele)
                if band_deform_method == 'rigid':
                    for i_e in range(n_e):
                        ele_nodes = ele[i_e].nodes
                        for i_n in ele_nodes:
                            xx = nodes[i_n - 1]
                            angle_x = np.arctan2(xx[1], xx[0])  # [-pi, pi]
                            gore_id = int((angle_x + 2 * np.pi) / theta) % (2 * n)
                            # For the piece  [pi/n * gore_id, pi/n * (gore_id + 1)]
                            # map the point xx -> rot_A * xx  + disp

                            band_rot = band_rot_matrices[gore_id]
                            band_disp = band_disp_vectors[gore_id]
                            new_xx = np.dot(band_rot, xx) + band_disp

                            node_disp[i_n - 1, :] = new_xx[0] - xx[0], new_xx[1] - xx[1], new_xx[2] - xx[2]
                elif band_deform_method == 'flat':

                    l_b_deform = theta * R_b
                    R_b_deform = r_b_deform * np.cos(theta) - np.sqrt(
                        l_b_deform * l_b_deform - r_b_deform * r_b_deform * np.sin(theta) * np.sin(theta))

                    for i_e in range(n_e):
                        ele_nodes = ele[i_e].nodes
                        for i_n in ele_nodes:
                            xx = nodes[i_n - 1]
                            angle_x = np.arctan2(xx[1], xx[0])  # [-pi, pi]
                            gore_id = int((angle_x + 2 * np.pi) / theta) % (2 * n)
                            # For the piece  [pi/n * gore_id, pi/n * (gore_id + 1)]
                            # map the point xx -> rot_A * xx  + disp

                            d_theta = angle_x - gore_id * theta if angle_x >= 0 else angle_x + 2 * np.pi - gore_id * theta
                            assert (d_theta <= theta and d_theta >= 0)
                            ds = d_theta * R_b

                            start_deform = np.empty(3)
                            end_deform = np.empty(3)
                            if gore_id % 2 == 0:
                                start_deform[:] = R_b_deform * np.cos(gore_id * theta), R_b_deform * np.sin(
                                    gore_id * theta), 0
                                end_deform[:] = r_b_deform * np.cos((gore_id + 1) * theta), r_b_deform * np.sin(
                                    (gore_id + 1) * theta), 0
                            else:  # gore_id%2 == 1
                                start_deform[:] = r_b_deform * np.cos(gore_id * theta), r_b_deform * np.sin(
                                    gore_id * theta), 0
                                end_deform[:] = R_b_deform * np.cos((gore_id + 1) * theta), R_b_deform * np.sin(
                                    (gore_id + 1) * theta), 0

                            new_xx = (1 - ds / l_b_deform) * start_deform + ds / l_b_deform * end_deform
                            new_xx[2] = xx[2] + band_b3

                            node_disp[i_n - 1, :] = new_xx[0] - xx[0], new_xx[1] - xx[1], new_xx[2] - xx[2]

        ##############################################################################################################
        # Update suspension lines
        ##############################################################################################################
        for i_es in range(n_es):
            ele = ele_set[i_es]
            ele_info = ele_set_info[i_es]
            if ele_info[1] == 2 and (ele_info[0] == 'Suspension_Lines' or ele_info[0] == 'Vent_Lines' or ele_info[0] == 'Gap_Lines'):
                l_ref = -1.0
                if  ele_info[0] == 'Suspension_Lines':
                    l_ref = L_s
                elif ele_info[0] == 'Vent_Lines':
                    l_ref = L_v
                elif ele_info[0] == 'Gap_Lines':
                    l_ref = L_g

                print('handle suspension lines')
                lines = SplitLines(ele)
                print('line number is ', len(lines))
                for i_line in range(len(lines)):
                    line = lines[i_line]
                    xx_start = np.array(nodes[line[0] - 1])
                    start_deform = np.array(nodes[line[0] - 1]) + node_disp[line[0] - 1,:]
                    end_deform   = np.array(nodes[line[-1] - 1]) + node_disp[line[-1] - 1,:]

                    cur_length = np.linalg.norm(end_deform - start_deform)

                    if cur_length >= l_ref :
                        print('current lenght is ', cur_length, ' , which is greater than its undeformed length ', l_ref)

                        for i_n in range(len(line)):
                            xx = nodes[line[i_n] - 1]

                            new_xx = (1. - float(i_n) / float(len(line) - 1)) * start_deform + float(i_n) / float(len(line) - 1) * end_deform

                            node_disp[line[i_n] - 1, :] = new_xx[0] - xx[0], new_xx[1] - xx[1], new_xx[2] - xx[2]
                    else:
                        print('current lenght is ', cur_length, ' , which is smaller than its undeformed length ', l_ref)

                        # use catenary curve fitting
                        #todo check start, end and z-axis are on the same plane


                        angle_x = np.arctan2(start_deform[1], start_deform[0]) \
                            if start_deform[0] ** 2 + start_deform[1] ** 2 > end_deform[0] ** 2 + end_deform[1] ** 2   \
                            else np.arctan2(end_deform[1], end_deform[0])  # [-pi, pi]

                        start_deform_2d = np.array([start_deform[0]*np.cos(angle_x) + start_deform[1]*np.sin(angle_x), start_deform[2]])
                        end_deform_2d   = np.array([end_deform[0]*np.cos(angle_x) + end_deform[1]*np.sin(angle_x), end_deform[2]])

                        print(np.sqrt(start_deform[0]**2 + start_deform[1]**2), ' ', start_deform[0] * np.cos(angle_x) + start_deform[1] * np.sin(angle_x))
                        print(np.sqrt(end_deform[0] ** 2 + end_deform[1] ** 2), ' ',
                              end_deform[0] * np.cos(angle_x) + end_deform[1] * np.sin(angle_x))

                        if line_relax_method == 'circle':
                            print('have not implemented yet')

                            # a = fsolve(catenary, (cur_length/l_ref), np.sqrt(12 * (1. - cur_length/l_ref)))[0]
                            # line_R = l_ref / line_theta
                            # circle_O =
                            # for i_n in range(len(line)):
                            #     d_theta = float(i_n) / float(len(line)) * line_theta
                            #
                            #
                            #     new_xx = (1. - float(i_n) / float(len(line))) * start_deform + float(i_n) / float(
                            #         len(line)) * end_deform
                            #
                            #     node_disp[line[i_n] - 1, :] = new_xx[0] - xx[0], new_xx[1] - xx[1], new_xx[2] - xx[2]

                        elif line_relax_method == 'catenary':

                            a, xm, ym = Catenary.catenary(start_deform_2d[0], start_deform_2d[1], end_deform_2d[0], end_deform_2d[1], l_ref)

                            for i_n in range(len(line)):
                                xx = np.array(nodes[line[i_n] - 1])
                                ds = np.linalg.norm(xx - xx_start)
                                new_r, new_z = Catenary.point_on_catenary(start_deform_2d[0], start_deform_2d[1], end_deform_2d[0], end_deform_2d[1], a, xm, ym, l_ref, ds)

                                new_xx = np.array([new_r*np.cos(angle_x), new_r*np.sin(angle_x),new_z])

                                node_disp[line[i_n] - 1, :] = new_xx[0] - xx[0], new_xx[1] - xx[1], new_xx[2] - xx[2]





        self.node_disp = node_disp






if __name__ == '__main__':
    mesh = Mesh()

    mesh.read_stru('Parachute_Quad_Init/mesh_Structural.top.quad')

    #mesh.refine()
    mesh.folding(8)
    mesh.visualize_disp()
    mesh.write_stru('mesh_Structural.top.quad', 'mesh_Structural.surfacetop.quad')







