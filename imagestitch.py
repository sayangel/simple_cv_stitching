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
    print(img1_path)

    img2_path = tkFileDialog.askopenfilename(message="Select Top Right Image")
    print(img2_path)

    img3_path = tkFileDialog.askopenfilename(message="Select Bottom Left Image")
    print(img3_path)

    img4_path = tkFileDialog.askopenfilename(message="Select Bottom Right Image")
    print(img4_path)

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
    print(img1_path)

    img2_path = tkFileDialog.askopenfilename(message="Select Right/Bottom Image")
    print(img2_path)

    #open image structures from file path
    img1 = Image(img1_path)
    img2 = Image(img2_path)

    #append to the image list
    img_array.append(img1)
    img_array.append(img2)

input_img_list = []
open_images(input_img_list)
print len(input_img_list) > 3
if len(input_img_list) > 2:
  multiple = True
else:
  multiple = False
  
img1 = input_img_list[0]
img2 = input_img_list[1]
if multiple:
  img3 = input_img_list[2]
  img4 = input_img_list[3]


#vertical and horizontal are multipliers for dimensions of the final image
#when stitching vertically/horizontally double the height/width
vertical = 1
horizontal = 1

#figure out orientation of stitching if only 2 images to determine dimensions
if not multiple:
  orientation = raw_input("Vertical (y/n): ")
  if orientation == "y" or orientation == "Y" or orientation == "yes" or orientation == "Yes":
    vertical = 2
  else:
    horizontal = 2


#create destination image
#ASSUMPTION: img1 and img2 have the same dimensions
dst = Image((img1.width*horizontal, img1.height*vertical))

print "Running findKeypointMatch..."

# Find the keypoints.
match_features = img1.findKeypointMatch(img2)

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
x = Image(
          #consider using warpAffine here since we can assume no 3D perspective change
          cv2.warpPerspective(
                              np.array((img2.getMatrix()))
                              , homo
                              , (dst_mat.rows, dst_mat.cols+300)
                              , np.array(dst_mat)
                              , cv2.INTER_CUBIC
                              )
          , colorSpace=ColorSpace.RGB
          ).toBGR()

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

# blit the img1 now on coordinate (0, 0).
x = x.blit(img1, alpha=0.5)
x.save("finish.jpg")
