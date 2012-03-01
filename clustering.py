#!/usr/bin/env python

'''

Algorithms for clustering edges into connected components
http://en.wikipedia.org/wiki/Connected_component_(graph_theory)
Handles undirected edges with or without edge weights.  
'''


import util


def returnOneClass(node):
    ''' 
    Default node classification function.  All nodes belong to the same
    class: 1.
    '''
    return 1


class SimpleEdgeClusterer:
    def __init__(self):
        self.clusterIdToNodes = {}
        self.nodeIdToClusterId = {}
        self.nextClusterId = 1

    def cluster(self, edge):
        '''
        edge: seq of (fromNodeId, toNodeId, ...)
        returns: nothing.
        '''
        # The following is an incremental single-linkage clustering algorithm which treats edges as undirected.
        
        (fromNodeId, toNodeId) = edge[0:2]
        
        # get cluster ids of the nodes
        fromNodeClusterId = None
        toNodeClusterId = None
        if self.nodeIdToClusterId.has_key(fromNodeId):
            fromNodeClusterId = self.nodeIdToClusterId[fromNodeId]
        if self.nodeIdToClusterId.has_key(toNodeId):
            toNodeClusterId = self.nodeIdToClusterId[toNodeId]
            
        # add edge to a new cluster
        if not fromNodeClusterId and not toNodeClusterId:
            self.clusterIdToNodes[self.nextClusterId] = set([fromNodeId, toNodeId])
            self.nodeIdToClusterId[fromNodeId] = self.nextClusterId
            self.nodeIdToClusterId[toNodeId] = self.nextClusterId
            self.nextClusterId += 1
            
        # add missing node and edge to the existing cluster
        elif (not fromNodeClusterId and toNodeClusterId) or (fromNodeClusterId and not toNodeClusterId):
            if fromNodeClusterId:
                missingNodeId, presentClusterId = toNodeId, fromNodeClusterId
            else:
                missingNodeId, presentClusterId = fromNodeId, toNodeClusterId
            self.nodeIdToClusterId[missingNodeId] = presentClusterId
            self.clusterIdToNodes[presentClusterId].add(missingNodeId)
                
        # do nothing if both nodes already belong to the same cluster
        elif fromNodeClusterId == toNodeClusterId:
            pass

        # unify clusters of nodes
        else: # fromNodeClusterId != toNodeClusterId
            # smallerClusterId, largerClusterId = fromNodeClusterId, toNodeClusterId
            if len(self.clusterIdToNodes[fromNodeClusterId]) < len(self.clusterIdToNodes[toNodeClusterId]):
                smallerClusterId, largerClusterId = fromNodeClusterId, toNodeClusterId
            else:
                smallerClusterId, largerClusterId = toNodeClusterId, fromNodeClusterId
            # change the clusterId of one the smaller set of nodes
            for nodeId in self.clusterIdToNodes[smallerClusterId]:
                self.nodeIdToClusterId[nodeId] = largerClusterId
            # remove the smaller clusterId stuff from the lookups, adding them to the larger cluster
            self.clusterIdToNodes[largerClusterId].update(self.clusterIdToNodes.pop(smallerClusterId))


class EdgeClusterer:
    '''
    Clusters nodes based on undirected edges into connected components.
    It performs single-linkage clustering of undirected edges.
    It also keeps statistics on distances of edges in clusters.  
    Also keeps track of the classes of nodes in clusters,
    if a classification function is given.
    For example, if you are clustering genes, the class might be the genome
    of the gene.
    '''
    def __init__(self, classifyNodeFunc=returnOneClass, storeEdges=False):
        self.clusterIdToNodes = {}
        self.nodeIdToClusterId = {}
        self.nextClusterId = 1
        self.clusterIdToSumDistances = {}
        self.clusterIdToNumEdges = {}
        self.clusterIdToNodeClasses = {}
        self.classifyNode = classifyNodeFunc
        self.storeEdges = storeEdges
        self.clusterIdToEdges = {}

    def cluster(self, edge):
        '''
        edge: seq of (fromNodeId, toNodeId, distance)
        returns: nothing.
        '''
        # The  following is a description of the algorithm used to build clusters.
        # This algorithm is generic and can be used to build clusters (connected subgraphs) from any graph.
        # It builds the clusters by iterating over every edge in the graph.  An edge is a triple of (node1, node2, distance).
        # There are 4 ways an edge can be added:
        # 1. Both nodes are not a part of a cluster, in which case a new cluster is created and each node is added to it.
        # 2. Exactly one node is part of a cluster, in which case the other node is added to the cluster already containing one of the nodes.
        # 3. Both nodes are part of the same cluster, in which case do nothing.
        # 4. Both nodes are part of different clusters, in which case merge the smaller cluster into the larger cluster.
        # As clusters are being built, various statistics are kept track of, such as the number of edges in a cluster.
        # It has the facility to track the classes of nodes in a cluster, if a mapping from node to class is given.
        # 
        # Complexity analysis: let n be the number of nodes.  Then the number of edges is O(n^2).  And the number of clusters, since each node can be in at
        # most one cluster and clusters always contain at least 2 nodes, is O(n).  (Note: since genomes/classes have 10k-30k nodes roughly, the # of genomes
        # is another way to analyze complexity.)
        # The loop over the edges takes O(n^2) time.  Merging a cluster is more complicated.  Essentially, it takes n binary merges to unify n clusters
        # into one cluster.  For each merge the nodes in the smaller cluster are iterated through to add to the larger cluster.  So the time complexity is
        # worst when balanced merges are occurring.  There are n-1 balanced merges in the "merge tree" (draw a binary tree representing the merges), and at
        # any level l there are 2^l merges of clusters of size <= n/2^(l+1).  Which the worst case for merging would take nlogn time total, amortized somehow
        # over the loop over edges.
        # space complexity: node to cluster id map takes up O(n) space.  since clusters are O(n) and each node is in only one cluster, the clusterIdsToNodes
        # map also uses O(n) space.
        # Overall Complexity: Time = O(n^2), Space = O(n)
        
        # self.numEdges += 1
        (fromNodeId, toNodeId, distance) = edge
        
        # get cluster ids of the nodes
        fromNodeClusterId = None
        toNodeClusterId = None
        if self.nodeIdToClusterId.has_key(fromNodeId):
            fromNodeClusterId = self.nodeIdToClusterId[fromNodeId]
        if self.nodeIdToClusterId.has_key(toNodeId):
            toNodeClusterId = self.nodeIdToClusterId[toNodeId]
            
        # add edge to a new cluster
        if not fromNodeClusterId and not toNodeClusterId:
            self.clusterIdToNodes[self.nextClusterId] = set([fromNodeId, toNodeId])
            self.clusterIdToNodeClasses[self.nextClusterId] = set([self.classifyNode(fromNodeId), self.classifyNode(toNodeId)])
            self.clusterIdToSumDistances[self.nextClusterId] = distance
            self.clusterIdToNumEdges[self.nextClusterId] = 1
            self.nodeIdToClusterId[fromNodeId] = self.nextClusterId
            self.nodeIdToClusterId[toNodeId] = self.nextClusterId
            if self.storeEdges:
                self.clusterIdToEdges[self.nextClusterId] = [edge]
            self.nextClusterId += 1
            
        # add missing node and edge to the existing cluster
        elif (not fromNodeClusterId and toNodeClusterId) or (fromNodeClusterId and not toNodeClusterId):
            if fromNodeClusterId:
                missingNodeId, presentClusterId = toNodeId, fromNodeClusterId
            else:
                missingNodeId, presentClusterId = fromNodeId, toNodeClusterId
            self.nodeIdToClusterId[missingNodeId] = presentClusterId
            self.clusterIdToNodes[presentClusterId].add(missingNodeId)
            self.clusterIdToNodeClasses[presentClusterId].add(self.classifyNode(missingNodeId))
            self.clusterIdToSumDistances[presentClusterId] += distance
            self.clusterIdToNumEdges[presentClusterId] += 1
            if self.storeEdges:
                self.clusterIdToEdges[presentClusterId].append(edge)
                
        # do nothing if both nodes already belong to the same cluster
        elif fromNodeClusterId == toNodeClusterId:
            self.clusterIdToSumDistances[fromNodeClusterId] += distance
            self.clusterIdToNumEdges[fromNodeClusterId] += 1
            if self.storeEdges:
                self.clusterIdToEdges[fromNodeClusterId].append(edge)
            pass

        # unify clusters of nodes
        else: # fromNodeClusterId != toNodeClusterId
            # smallerClusterId, largerClusterId = fromNodeClusterId, toNodeClusterId
            if len(self.clusterIdToNodes[fromNodeClusterId]) < len(self.clusterIdToNodes[toNodeClusterId]):
                smallerClusterId, largerClusterId = fromNodeClusterId, toNodeClusterId
            else:
                smallerClusterId, largerClusterId = toNodeClusterId, fromNodeClusterId
            # change the clusterId of one the smaller set of nodes
            for nodeId in self.clusterIdToNodes[smallerClusterId]:
                self.nodeIdToClusterId[nodeId] = largerClusterId
            # remove the smaller clusterId stuff from the lookups, adding them to the larger cluster
            self.clusterIdToNodes[largerClusterId].update(self.clusterIdToNodes.pop(smallerClusterId))
            self.clusterIdToNodeClasses[largerClusterId].update(self.clusterIdToNodeClasses.pop(smallerClusterId))
            self.clusterIdToSumDistances[largerClusterId] += distance + self.clusterIdToSumDistances.pop(smallerClusterId)
            self.clusterIdToNumEdges[largerClusterId] += 1 + self.clusterIdToNumEdges.pop(smallerClusterId)
            if self.storeEdges:
                self.clusterIdToEdges[largerClusterId].extend(self.clusterIdToEdges[smallerClusterId])


def fileEdgeGen(path):
    ''' iterate over a file of edges '''
    with open(path) as fh:
        for id1, id2, dist in linesEdgeGen(fh):
            yield id1, id2, dist


def linesEdgeGen(lines):
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        id1, id2, distance = line.split()
        yield id1, id2, float(distance)


def test():

    input = '''
# columns: node1 node2 edge_distance
a b 1
a c 3
a d 3
a d 2
b e 1
f g 1
g h 1.5
'''
    # use clusterer that handles distances of edges.
    clusterer = EdgeClusterer()

    numEdges = 0
    for edge in linesEdgeGen(input.splitlines()):
        # cluster the edge
        clusterer.cluster(edge)
        numEdges += 1
        
        # calculate statistics about clusters
        distance = edge[2]
        clusterIds = clusterer.clusterIdToNodes.keys()
        numClusters = len(clusterIds)
        numNodes = len(clusterer.nodeIdToClusterId)

        avgDistances = [clusterer.clusterIdToSumDistances[id]/clusterer.clusterIdToNumEdges[id] for id in clusterIds]
        maxAvgDist = max(avgDistances)
        minAvgDist = min(avgDistances)
        avgAvgDist = sum(avgDistances)/numClusters

        clusterIdToNumNodes = dict([(id, len(clusterer.clusterIdToNodes[id])) for id in clusterIds])
        # nodeCounts = [len(clusterer.clusterIdToNodes[id]) for id in clusterIds]
        nodeCounts = clusterIdToNumNodes.values()
        maxNodeCount = max(nodeCounts)
        minNodeCount = min(nodeCounts)
        avgNodeCount = sum(nodeCounts)/float(numClusters) # avoid integer division to get exact value

        edgeCounts = [clusterer.clusterIdToNumEdges[id] for id in clusterIds]
        maxEdgeCount = max(edgeCounts)
        minEdgeCount = min(edgeCounts)
        avgEdgeCount = sum(edgeCounts)/float(numClusters)

        classCounts = [len(clusterer.clusterIdToNodeClasses[id]) for id in clusterIds]
        bogusClassFound = int(True in [None in clusterer.clusterIdToNodeClasses[id] for id in clusterIds])
        maxClassCount = max(classCounts)
        minClassCount = min(classCounts)
        avgClassCount = sum(classCounts)/float(numClusters)

        tccs = [float(clusterer.clusterIdToNumEdges[id])/(clusterIdToNumNodes[id]*(clusterIdToNumNodes[id]-1)/2) for id in clusterIds]
        # tccs = [float(clusterer.clusterIdToNumEdges[id])/(len(clusterer.clusterIdToNodes[id])*(len(clusterer.clusterIdToNodes[id])-1)/2) for id in clusterIds]
        maxTcc = max(tccs)
        minTcc = min(tccs)
        avgTcc = sum(tccs)/numClusters
        
        # numPossibleTCEdges = sum([(n*(n-1))/2 for n in [len(genes) for genes in clusterer.clusterIdToNodes.values()]])
        numPossibleTCEdges = sum([(n*(n-1))/2 for n in nodeCounts])
        globalTcc = float(numEdges) / numPossibleTCEdges

        
        print '%.5f %s %s %s %.5f %.5f %.5f %.5f %.5f %.5f %.5f %s %s %.5f %s %s %.5f %s %s %.5f %s'%(distance, numClusters, numNodes, numEdges, globalTcc, minTcc, maxTcc, avgTcc, minAvgDist, maxAvgDist, avgAvgDist, minNodeCount, maxNodeCount, avgNodeCount, minEdgeCount, maxEdgeCount, avgEdgeCount, minClassCount, maxClassCount, avgClassCount, bogusClassFound)

if __name__ == '__main__':
    test()


# last line emacs python-mode bug fix.  do not cross line.
