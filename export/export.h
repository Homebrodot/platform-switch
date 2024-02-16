/**************************************************************************/
/*  export.h                                                              */
/**************************************************************************/
/*                         This file is part of:                          */
/*                              HOMEBRODOT                                */
/**************************************************************************/
/* Copyright (c) 2023-present Homebrodot contributors.                    */
/*                                                                        */
/* Permission is hereby granted, free of charge, to any person obtaining  */
/* a copy of this software and associated documentation files (the        */
/* "Software"), to deal in the Software without restriction, including    */
/* without limitation the rights to use, copy, modify, merge, publish,    */
/* distribute, sublicense, and/or sell copies of the Software, and to     */
/* permit persons to whom the Software is furnished to do so, subject to  */
/* the following conditions:                                              */
/*                                                                        */
/* The above copyright notice and this permission notice shall be         */
/* included in all copies or substantial portions of the Software.        */
/*                                                                        */
/* THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,        */
/* EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF     */
/* MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. */
/* IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY   */
/* CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,   */
/* TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE      */
/* SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.                 */
/**************************************************************************/

#ifndef SWITCH_EXPORT_H
#define SWITCH_EXPORT_H

#ifndef MODULE_MONO_ENABLED

#include "thirdparty/libnx/nacp.h"
#include "thirdparty/libnx/nro.h"
#include <cstring>
#include <string>

unsigned char *read_file(const char *fn, size_t *len_out);
unsigned char *read_bytes(const char *fn, size_t off, size_t len);
size_t write_bytes(const char *fn, size_t off, size_t len, const unsigned char *data);

void register_switch_exporter();

#endif // !MODULE_MONO_ENABLED

#endif // !SWITCH_EXPORT_H
