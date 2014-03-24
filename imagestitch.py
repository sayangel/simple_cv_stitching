from SimpleCV import *
import Tkinter, tkFileDialog
import cv2
import cv

root = Tkinter.Tk()
root.withdraw()

img1_path = tkFileDialog.askopenfilename(message="Select Left/Top Image")
print(img1_path)

img2_path = tkFileDialog.askopenfilename(message="Select Right/Bottom Image")
print(img2_path)


img1 = Image(img1_path)
img2 = Image(img2_path)

#create destination image
#ASSUMPTION: img1 and img2 have the same dimensions
dst = Image((img1.width*2, img1.height))

print "Running findKeypointMatch..."
lo = 0
hi = 1
for x in range(lo, hi):
  print "findKeypointmatch %d of %d" %(x+1, hi)
  # Find the keypoints.
  match_features = img1.findKeypointMatch(img2)
  print match_features[0]

  x = match_features[0].topLeftCorner()[0]
  y = match_features[0].topLeftCorner()[1]
  w = match_features[0].width()
  h = match_features[0].height()

  # print match_features[0].getMinRect()
  # print "x: %d" %(x)
  # print "y: %d" %(y)
  # print "w: %d" %(w)
  # print "h: %d" %(h)

  # The homography matrix.
  homo = match_features[0].getHomography()
  # homo[2][0] = 0
  # homo[2][1] = 0
  # homo[2][2] = 1

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
