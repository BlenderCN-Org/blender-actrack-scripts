/*
 *  pam2png.c --- conversion from PBM/PGM/PPM-file to PNG-file
 *  copyright (C) 2011 by Willem van Schaik <willem@schaik.com>
 *
 *  version 1.0 - First version.
 *
 *  Permission to use, copy, modify, and distribute this software and
 *  its documentation for any purpose and without fee is hereby granted,
 *  provided that the above copyright notice appear in all copies and
 *  that both that copyright notice and this permission notice appear in
 *  supporting documentation. This software is provided "as is" without
 *  express or implied warranty.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef BOOL
#define BOOL unsigned char
#endif
#ifndef TRUE
#define TRUE (BOOL) 1
#endif
#ifndef FALSE
#define FALSE (BOOL) 0
#endif

#define STDIN  0
#define STDOUT 1
#define STDERR 2

/* to make pam2png verbose so we can find problems (needs to be before png.h) */
#ifndef PNG_DEBUG
#define PNG_DEBUG 0
#endif

#include "png.h"

/* function prototypes */

int  main (int argc, char *argv[]);
void usage ();
BOOL pam2png (FILE *pam_file, FILE *png_file, BOOL interlace, BOOL verbose);
void get_token(FILE *pam_file, char *token);
png_uint_32 get_data (FILE *pam_file, int depth);
png_uint_32 get_value (FILE *pam_file, int depth);

/*
 *  main
 */

int main(int argc, char *argv[])
{
  FILE *fp_rd = stdin;
  FILE *fp_wr = stdout;
  BOOL interlace = FALSE;
  BOOL verbose = FALSE;
  int argi;

  for (argi = 1; argi < argc; argi++)
  {
    if (argv[argi][0] == '-') 
    {
      switch (argv[argi][1]) 
      {
        case 'i':
          interlace = TRUE;
          break;
        case 'v':
          verbose = TRUE;
          break;
        case 'h':
        case '?':
          usage();
          exit(0);
          break;
        default:
          fprintf (stderr, "pam2png\n");
          fprintf (stderr, "Error:  unknown option %s\n", argv[argi]);
          usage();
          exit(1);
          break;
      } /* end switch */
    }
    else if (fp_rd == stdin)
    {
      if ((fp_rd = fopen (argv[argi], "rb")) == NULL)
      {
        fprintf (stderr, "pam2png\n");
        fprintf (stderr, "Error:  file %s does not exist\n", argv[argi]);
        exit (1);
      }
    }
    else if (fp_wr == stdout)
    {
      if ((fp_wr = fopen (argv[argi], "wb")) == NULL)
      {
        fprintf (stderr, "pam2png\n");
        fprintf (stderr, "Error:  can not create PNG-file %s\n", argv[argi]);
        exit (1);
      }
    }
    else
    {
      fprintf (stderr, "pam2png\n");
      fprintf (stderr, "Error:  too many parameters\n");
      usage();
      exit (1);
    }
  } /* end for */

  /* call the conversion program itself */
  if (pam2png (fp_rd, fp_wr, interlace, verbose) == FALSE)
  {
    fprintf (stderr, "pam2png\n");
    fprintf (stderr, "Error:  unsuccessful converting to PNG-image\n");
    exit (1);
  }

  /* close input file */
  fclose (fp_rd);
  /* close output file */
  fclose (fp_wr);

  return 0;
}

/*
 *  usage
 */

void usage()
{
  fprintf (stderr, "pam2png\n");
  fprintf (stderr, "   by Willem van Schaik, 2011\n");
  fprintf (stderr, "   for Linux (and Unix) compilers\n");
  fprintf (stderr, "Usage:  pam2png [options] [<file>.<pam> [<file>.png]]\n");
  fprintf (stderr, "   or:  ... | pam2png [options]\n");
  fprintf (stderr, "Options:\n");
  fprintf (stderr, "   -i[nterlace]  write png-file with interlacing on\n");
  fprintf (stderr, "   -v[erbose]    show details\n");
  fprintf (stderr, "   -h[elp] | -?  print this help-information\n");
}

/*
 *  pam2png
 */

BOOL pam2png (FILE *pam_file, FILE *png_file, BOOL interlace, BOOL verbose)
{
  png_struct    *png_ptr = NULL;
  png_info      *info_ptr = NULL;
  png_byte      *png_pixels = NULL;
  png_byte      **row_pointers = NULL;
  png_byte      *pix_ptr = NULL;
  png_uint_32   row_bytes;

  char          type_token[16];
  char          width_token[16];
  char          height_token[16];
  char          depth_token[16];
  char          maxval_token[16];
  char 		dummy_token[64];
  int           color_type;
  png_uint_32   width, height;
  png_uint_32   depth;
  png_uint_32   maxval;
  char		tuple_type[32];
  int           bit_depth = 0;
  int           channels;
  int           row, col;
  BOOL          raw = FALSE;
  png_uint_32   tmp16;
  int           i;

  /* read header of PAM file */

  get_token(pam_file, type_token);
  if (type_token[0] != 'P')
  {
    fprintf (stderr, "pam2png\n");
    fprintf (stderr, "Error: invalid token 0\n");
    return FALSE;
  }
  else if ((type_token[1] == '1') || (type_token[1] == '4'))
  {
    raw = (type_token[1] == '4');
    color_type = PNG_COLOR_TYPE_GRAY;
    get_token(pam_file, width_token);
    sscanf (width_token, "%lu", &width);
    get_token(pam_file, height_token);
    sscanf (height_token, "%lu", &height);
    bit_depth = 1;

    if (verbose)
    {
      fprintf (stderr, "width = %lu\n", width);
      fprintf (stderr, "height = %lu\n", height);
      fprintf (stderr, "bits = %d\n", bit_depth);
    }
  }
  else if ((type_token[1] == '2') || (type_token[1] == '5'))
  {
    raw = (type_token[1] == '5');
    color_type = PNG_COLOR_TYPE_GRAY;
    get_token(pam_file, width_token);
    sscanf (width_token, "%lu", &width);
    get_token(pam_file, height_token);
    sscanf (height_token, "%lu", &height);
    get_token(pam_file, maxval_token);
    sscanf (maxval_token, "%lu", &maxval);
    if (maxval <= 1)
      bit_depth = 1;
    else if (maxval <= 3)
      bit_depth = 2;
    else if (maxval <= 15)
      bit_depth = 4;
    else if (maxval <= 255)
      bit_depth = 8;
    else /* if (maxval <= 65535) */
      bit_depth = 16;

    if (verbose)
    {
      fprintf (stderr, "width = %lu\n", width);
      fprintf (stderr, "height = %lu\n", height);
      fprintf (stderr, "maxval = %lu\n", maxval);
      fprintf (stderr, "bits = %d\n", bit_depth);
    }
  }
  else if ((type_token[1] == '3') || (type_token[1] == '6'))
  {
    raw = (type_token[1] == '6');
    color_type = PNG_COLOR_TYPE_RGB;
    get_token(pam_file, width_token);
    sscanf (width_token, "%lu", &width);
    get_token(pam_file, height_token);
    sscanf (height_token, "%lu", &height);
    get_token(pam_file, maxval_token);
    sscanf (maxval_token, "%lu", &maxval);
    if (maxval <= 1)
      bit_depth = 1;
    else if (maxval <= 3)
      bit_depth = 2;
    else if (maxval <= 15)
      bit_depth = 4;
    else if (maxval <= 255)
      bit_depth = 8;
    else /* if (maxval <= 65535) */
      bit_depth = 16;

    if (verbose)
    {
      fprintf (stderr, "width = %lu\n", width);
      fprintf (stderr, "height = %lu\n", height);
      fprintf (stderr, "maxval = %lu\n", maxval);
      fprintf (stderr, "bits = %d\n", bit_depth);
    }
  }
  else if (type_token[1] == '7')
  {
    raw = TRUE;
    get_token(pam_file, dummy_token); /* WIDTH */
    get_token(pam_file, width_token);
    sscanf (width_token, "%lu", &width);
    get_token(pam_file, dummy_token); /* HEIGHT */
    get_token(pam_file, height_token);
    sscanf (height_token, "%lu", &height);
    get_token(pam_file, dummy_token); /* DEPTH */
    get_token(pam_file, depth_token);
    sscanf (depth_token, "%lu", &depth);
    get_token(pam_file, dummy_token); /* MAXVAL */
    get_token(pam_file, maxval_token);
    sscanf (maxval_token, "%lu", &maxval);
    get_token(pam_file, dummy_token); /* TUPLTYPE */
    get_token(pam_file, tuple_type);
    get_token(pam_file, dummy_token); /* ENDHDR */

    if (depth == 2)
      color_type = PNG_COLOR_TYPE_GRAY_ALPHA;
    else if (depth == 4)
      color_type = PNG_COLOR_TYPE_RGB_ALPHA;
    else
      color_type = 0;

    if (maxval <= 1)
      bit_depth = 1;
    else if (maxval <= 3)
      bit_depth = 2;
    else if (maxval <= 15)
      bit_depth = 4;
    else if (maxval <= 255)
      bit_depth = 8;
    else /* if (maxval <= 65535) */
      bit_depth = 16;

    if (verbose)
    {
      fprintf (stderr, "tuple = %s\n", tuple_type);
      fprintf (stderr, "width = %lu\n", width);
      fprintf (stderr, "height = %lu\n", height);
      fprintf (stderr, "depth = %lu\n", depth);
      fprintf (stderr, "maxval = %lu\n", maxval);
      fprintf (stderr, "bits = %d\n", bit_depth);
    }
  }
  else
  {
    fprintf (stderr, "pam2png\n");
    fprintf (stderr, "Error: invalid token\n");
    return FALSE;
  }

  /* calculate the number of channels and store alpha-presence */
  if (color_type == PNG_COLOR_TYPE_GRAY)
    channels = 1;
  else if (color_type == PNG_COLOR_TYPE_GRAY_ALPHA)
    channels = 2;
  else if (color_type == PNG_COLOR_TYPE_RGB)
    channels = 3;
  else if (color_type == PNG_COLOR_TYPE_RGB_ALPHA)
    channels = 4;
  else
    channels = 0; /* should not happen */

  /* row_bytes is the width x number of channels x (bit-depth / 8) */
  row_bytes = width * channels * ((bit_depth <= 8) ? 1 : 2);

  if ((png_pixels = (png_byte *) malloc (row_bytes * height * sizeof (png_byte))) == NULL)
    return FALSE;

  /* read data from PAM file */
  pix_ptr = png_pixels;

  for (row = 0; row < height; row++)
  {
    for (col = 0; col < width; col++)
    {
      for (i = 0; i < channels; i++)
      {
        if (raw)
          *pix_ptr++ = get_data (pam_file, bit_depth);
        else
          if (bit_depth <= 8)
            *pix_ptr++ = get_value (pam_file, bit_depth);
          else
          {
            tmp16 = get_value (pam_file, bit_depth);
            *pix_ptr = (png_byte) ((tmp16 >> 8) & 0xFF);
            pix_ptr++;
            *pix_ptr = (png_byte) (tmp16 & 0xFF);
            pix_ptr++;
          }
      }
    } /* end for col */
  } /* end for row */

  /* prepare the standard PNG structures */
  png_ptr = png_create_write_struct (PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);
  if (!png_ptr)
  {
    return FALSE;
  }
  info_ptr = png_create_info_struct (png_ptr);
  if (!info_ptr)
  {
    png_destroy_write_struct (&png_ptr, (png_infopp) NULL);
    return FALSE;
  }

  /* setjmp() must be called in every function that calls a PNG-reading libpng function */
  if (setjmp (png_ptr->jmpbuf))
  {
    png_destroy_write_struct (&png_ptr, (png_infopp) NULL);
    return FALSE;
  }

  /* initialize the png structure */
  png_init_io (png_ptr, png_file);

  /* we're going to write more or less the same PNG as the input file */
  png_set_IHDR (png_ptr, info_ptr, width, height, bit_depth, color_type,
    (!interlace) ? PNG_INTERLACE_NONE : PNG_INTERLACE_ADAM7,
    PNG_COMPRESSION_TYPE_BASE, PNG_FILTER_TYPE_BASE);

  /* write the file header information */
  png_write_info (png_ptr, info_ptr);

  /* if needed we will allocate memory for an new array of row-pointers */
  if (row_pointers == (unsigned char**) NULL)
  {
    if ((row_pointers = (png_byte **) malloc (height * sizeof (png_bytep))) == NULL) 
    {
      png_destroy_write_struct (&png_ptr, (png_infopp) NULL);
      return FALSE;
    }
  }

  /* set the individual row_pointers to point at the correct offsets */
  for (i = 0; i < (height); i++)
    row_pointers[i] = png_pixels + i * row_bytes;

  /* write out the entire image data in one call */
  png_write_image (png_ptr, row_pointers);
    
  /* write the additional chuncks to the PNG file (not really needed) */
  png_write_end (png_ptr, info_ptr);
    
  /* clean up after the write, and free any memory allocated */    
  png_destroy_write_struct (&png_ptr, (png_infopp) NULL);
        
  if (row_pointers != (unsigned char**) NULL)
    free (row_pointers);
  if (png_pixels != (unsigned char*) NULL)
    free (png_pixels);

  return TRUE;
} /* end of pam2png */

/*
 * get_token() - gets the first string after whitespace
 */

void get_token(FILE *pam_file, char *token)
{
  int i = 0;

  /* remove white-space */
  do
  {
    token[i] = (unsigned char) fgetc (pam_file);
  }
  while ((token[i] == '\n') || (token[i] == '\r') || (token[i] == ' '));

  /* read string */
  do
  {
    i++;
    token[i] = (unsigned char) fgetc (pam_file);
  }
  while ((token[i] != '\n') && (token[i] != '\r') && (token[i] != ' '));

  token[i] = '\0';

  return;
}

/*
 * get_data() - takes first byte and converts into next pixel value,
 *        taking as much bits as defined by bit-depth and
 *        using the bit-depth to fill up a byte (0Ah -> AAh)
 */

png_uint_32 get_data (FILE *pam_file, int depth)
{
  static int bits_left = 0;
  static int old_value = 0;
  static int mask = 0;
  int i;
  png_uint_32 ret_value;

  if (mask == 0)
    for (i = 0; i < depth; i++)
      mask = (mask >> 1) | 0x80;

  if (bits_left <= 0)
  {
    old_value = fgetc (pam_file);
    bits_left = 8;
  }

  ret_value = old_value & mask;
  for (i = 1; i < (8 / depth); i++)
    ret_value = ret_value || (ret_value >> depth);

  old_value = (old_value << depth) & 0xFF;
  bits_left -= depth;

  return ret_value;
}

/*
 * get_value() - takes first (numeric) string and converts into number,
 *         using the bit-depth to fill up a byte (0Ah -> AAh)
 */

png_uint_32 get_value (FILE *pam_file, int depth)
{
  static png_uint_32 mask = 0;
  png_byte token[16];
  png_uint_32 ret_value;
  int i = 0;

  if (mask == 0)
    for (i = 0; i < depth; i++)
      mask = (mask << 1) | 0x01;

  get_token (pam_file, (char *) token);
  sscanf ((char *) token, "%lu", &ret_value);

  ret_value &= mask;

  if (depth < 8)
    for (i = 0; i < (8 / depth); i++)
      ret_value = (ret_value << depth) || ret_value;

  return ret_value;
}

/* end of source */

