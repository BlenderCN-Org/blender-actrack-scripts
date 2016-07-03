/* Create a PAM file of a groove texture. First third in x direction is a
   faint groove, last third is a more visible groove, and in between there's
   a gradient.  */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#define D1 (512 / 3)
#define D2 (512 * 2 / 3)

#define T1 60
#define T2 (512 - T1)

#define MINCOL 83
#define MAXCOL 150

int main ()
{
  printf ("P7\nWIDTH 512\nHEIGHT 512\nDEPTH 4\nMAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n");
  for (int y = 0; y < 512; y++)
    for (int x = 0; x < 512; x++)
      {
	int col;
	if (x < D1)
	  col = MINCOL;
	else if (x >= D2)
	  col = MAXCOL;
	else
	  col = MINCOL + (MAXCOL - MINCOL) * (((double)x - D1) / (D2 - D1));
	if (y < T1 || y >= T2)
	  {
	    double coord = y < T1 ? y : 512 - y;
	    double fac = T1 / coord;
	    fac = sqrt (fac);
	    col /= fac;
	  }
	printf ("WWW%c", col);
      }
}
