/**************************************************************************/
/*  audio_driver_audren.h                                                 */
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

#pragma once
#ifndef AUDIO_DRIVER_AUDREN_H
#define AUDIO_DRIVER_AUDREN_H

#include "servers/audio_server.h"
#include "switch_wrapper.h"

#include "core/os/mutex.h"
#include "core/os/thread.h"

class AudioDriverAudren : public AudioDriver {
    Thread thread;
    Mutex mutex;

    LibnxAudioDriver audren_driver;
    AudioDriverWaveBuf audren_buffers[2];
    size_t audren_pool_size;
    void *audren_pool_ptr;
    unsigned int audren_buffer_size;
    unsigned int buffer_size;
    Vector<int32_t> samples_in;
    Vector<int16_t> samples_out;

    String device_name;
    String new_device;

    Error init_device();
    void finish_device();

    static void thread_func(void *p_udata);

    unsigned int mix_rate;
    SpeakerMode speaker_mode;
    int channels;

    bool active;
    bool thread_exited;
    mutable bool exit_thread;

public:
    const char *get_name() const {
        return "AUDREN";
    };

    virtual Error init();
    virtual void start();
    virtual int get_mix_rate() const;
    virtual SpeakerMode get_speaker_mode() const;
    virtual Array get_device_list();
    virtual String get_device();
    virtual void set_device(String device);
    virtual void lock();
    virtual void unlock();
    virtual void finish();

    AudioDriverAudren();
    ~AudioDriverAudren();
};

#endif // !AUDIO_DRIVER_AUDREN_H
