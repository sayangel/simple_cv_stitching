from SimpleCV import *
import Tkinter, tkFileDialog
import cv2
import cv


#open images and create simplecv image structures from provided paths
def open_images(img_array):

  root = Tkinter.Tk()
  root.withdraw()

  #determine if > 2 images
  #max supported right now is 4
  mul_images = raw_input("Multiple images? (y/n): ")

  if mul_images == "y" or mul_images == "Y" or mul_images == "yes" or mul_images == "Yes":
    img1_path = tkFileDialog.askopenfilename(message="Select Top Left Image")

    img2_path = tkFileDialog.askopenfilename(message="Select Top Right Image")

    img3_path = tkFileDialog.askopenfilename(message="Select Bottom Left Image")

    img4_path = tkFileDialog.askopenfilename(message="Select Bottom Right Image")

    #open image structures from file path
    img1 = Image(img1_path)
    img2 = Image(img2_path)
    img3 = Image(img3_path)
    img4 = Image(img4_path)

    #append to the image list
    img_array.append(img1)
    img_array.append(img2)
    img_array.append(img3)
    img_array.append(img4)

  else:
    img1_path = tkFileDialog.askopenfilename(message="Select Left/Top Image")

    img2_path = tkFileDialog.askopenfilename(message="Select Right/Bottom Image")

    #open image structures from file path
    img1 = Image(img1_path)
    img2 = Image(img2_path)

    #append to the image list
    img_array.append(img1)
    img_array.append(img2)

#stitch_images will stitch a left/right image by default
#pass vertical and horizontal parameters as needed to stitch images
def stitch_images(image1, image2, vertical=False, horizontal=True, transparency = 1.0, useMask = False):
  #vertical/horizontal dimension multiplier
  v = 1
  h = 1
  if vertical:
    v = 2
  if horizontal:
    h = 2

  #create destination image
  #ASSUMPTION: img1 and img2 have the same dimensions

  dst = Image((image1.width*h, image1.height*v))

  # Find the keypoints.
  match_features = image1.findKeypointMatch(image2)
  match_features[0].draw(width=5)

  #create and use mask to properly blit the (typically last) image
  blitMask = Image(dst.size())
  if useMask:
    #may need overlap here to get better stitching results
    topLeftX = match_features[0].getMinRect()[0][0]+250
    topLeftY = match_features[0].getMinRect()[0][1]+250
    width = match_features[0].getMinRect()[3][0]-match_features[0].getMinRect()[0][0]
    height = match_features[0].getMinRect()[1][1] - match_features[0].getMinRect()[0][1]

    #create a mask to ensure blit in the proper area
    dl = DrawingLayer(dst.size())
    dl.rectangle((topLeftX, topLeftY), (width, height), filled = True, color=Color.WHITE)
    blitMask.addDrawingLayer(dl)
    blitMask = blitMask.applyLayers()
    blitMask = blitMask.invert()
    blitMask.save("mask.jpg")
    # dl.circle((300,300), 80, filled = True, color = Color.WHITE)
  # The homography matrix.
  homo = match_features[0].getHomography()
  #Uncomment if want to prevent perspective shift
  # homo[2][0] = 0
  # homo[2][1] = 0
  # homo[2][2] = 1

  #only 2D translation and rotation.. I think
  affine_transform = np.array([homo[0], homo[1]])

  dst_mat = dst.getMatrix()

  # transform the image.
  # should crop out the overlapping parts to avoid weird darkening etc.
  # Image constructor: Image(source=None, camera=None, colorSpace=0, verbose=True, sample=False, cv2image=False, webp=False)
  # cv2.warpPerspective(src, M, dsize[, dst[, flags[, borderMode[, borderValue]]]])

  #warpPerspective Implementation
  stitched_image = Image(
            #consider using warpAffine here since we can assume no 3D perspective change
            cv2.warpPerspective(
                                np.array((image2.getMatrix()))
                                , homo
                                , (dst_mat.rows, dst_mat.cols)
                                , np.array(dst_mat)
                                , cv2.INTER_CUBIC
                                )
            , colorSpace=ColorSpace.RGB
            )#.toBGR()

  # AFFINE ONLY IMPLEMENTATION
  # Doesn't seem to work too well..
  # x = Image(
  #           #consider using warpAffine here since we can assume no 3D perspective change
  #           cv2.warpAffine(
  #                               np.array((img2.getMatrix()))
  #                               , affine_transform
  #                               , (dst_mat.rows, dst_mat.cols+300)
  #                               , np.array(dst_mat)
  #                               , cv2.INTER_CUBIC
  #                               )
  #           , colorSpace=ColorSpace.RGB
  #           ).toBGR()

  if useMask:
    stitched_image = stitched_image.blit(image1, mask=blitMask)
  else:
    stitched_image = stitched_image.blit(image1)

  return stitched_image

#getKeypointMatch finds the keypointmatches and returns an affine transformation matrix
def getKeypointMatch(src,template,quality=500.00,minDist=0.2,minMatch=0.4):

        try:
            import cv2
        except:
            warnings.warn("Can't Match Keypoints without OpenCV >= 2.3.0")
            return
        if template == None:
          return None


        fs = FeatureSet()
        skp,sd = src._getRawKeypoints(quality)
        tkp,td = template._getRawKeypoints(quality)
        if( skp == None or tkp == None ):
            warnings.warn("I didn't get any keypoints. Image might be too uniform or blurry." )
            return None

        template_points = float(td.shape[0])
        sample_points = float(sd.shape[0])
        magic_ratio = 1.00
        if( sample_points > template_points ):
            magic_ratio = float(sd.shape[0])/float(td.shape[0])

        idx,dist = src._getFLANNMatches(sd,td) # match our keypoint descriptors
        p = dist[:,0]
        result = p*magic_ratio < minDist #, = np.where( p*magic_ratio < minDist )
        pr = result.shape[0]/float(dist.shape[0])

        if( pr > minMatch and len(result)>4 ): # if more than minMatch % matches we go ahead and get the data
            lhs = []
            rhs = []
            for i in range(0,len(idx)):
                if( result[i] ):
                    lhs.append((tkp[i].pt[1], tkp[i].pt[0]))
                    rhs.append((skp[idx[i]].pt[0], skp[idx[i]].pt[1]))

            rhs_pt = np.array(rhs)
            lhs_pt = np.array(lhs)

            if( len(rhs_pt) < 16 or len(lhs_pt) < 16 ):
                return None

            #TO-DO: figure out correct format for lhs_pt and rhs_pt
            affineTransform = cv2.estimateRigidTransform(lhs_pt, rhs_pt, False)

            return affineTransform

            # homography = []
            # (homography,mask) = cv2.findHomography(lhs_pt,rhs_pt,cv2.RANSAC, ransacReprojThreshold=1.0 )
            # w = template.width
            # h = template.height
            #
            # pts = np.array([[0,0],[0,h],[w,h],[w,0]], dtype="float32")
            #
            # pPts = cv2.perspectiveTransform(np.array([pts]), homography)
            #
            # pt0i = (pPts[0][0][1], pPts[0][0][0])
            # pt1i = (pPts[0][1][1], pPts[0][1][0])
            # pt2i = (pPts[0][2][1], pPts[0][2][0])
            # pt3i = (pPts[0][3][1], pPts[0][3][0])
            #
            # #construct the feature set and return it.
            # fs = FeatureSet()
            # fs.append(KeypointMatch(self,template,(pt0i,pt1i,pt2i,pt3i),homography))
            # #the homography matrix is necessary for many purposes like image stitching.
            # #fs.append(homography) # No need to add homography as it is already being
            # #added in KeyPointMatch class.
            # #return fs
        else:
            return None




input_img_list = []
open_images(input_img_list)

if len(input_img_list) > 2:
  multiple = True
else:
  multiple = False

img1 = input_img_list[0]
img2 = input_img_list[1]
if multiple:
  img3 = input_img_list[2]
  img4 = input_img_list[3]


#vertical and horizontal are bools to determine multipliers for dimensions of the final image
#when stitching vertically/horizontally double the height/width
vertical = False
horizontal = False

if not multiple:
  #figure out orientation of stitching if only 2 images to determine dimensions
  orientation = raw_input("Vertical (y/n): ")
  if orientation == "y" or orientation == "Y" or orientation == "yes" or orientation == "Yes":
    vertical = True
  else:
    horizontal = True

  print "Stitching..."
  final = stitch_images(input_img_list[0], input_img_list[1], vertical, horizontal)
  final.save("stitched.jpg")
  print "Image saved as stitched.jpg"

if multiple:
  print "Stitching top left and top right..."
  #(1) stitch bottom left and right images - horizontal stitch
  first_stitch = stitch_images(input_img_list[0], input_img_list[1])

  print "Stitching top half with bottom left..."
  #(2) stitch above image with bottom left corner - vertical stitch
  second_stitch = stitch_images(first_stitch, input_img_list[2], True, False)

  print "Stitching bottom right to rest of image..."
  #(3) stitch above image with bottom left corner - no vertical no horizontal
  final = stitch_images(second_stitch, input_img_list[3], False, False, 0.5, True)
  final.save("stitched.jpg")
  print "Image saved as stitched.jpg"
