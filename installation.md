# otto
OTTO Tractor Configuration

## Video 4 Linux
```bash
sudo modprobe bcm2835-v4l2
```

## Learning System

Equipment: Nvidia TX2

Software Configuration

```bash
sudo apt-get install python3-pip
sudo apt-get install libfreetype6-dev
sudo apt-get install python3-h5py

time sudo pip3 install numpy 
time sudo pip3 install matplotlib
sudo pip3 install pyserial
sudo pip3 install pillow
sudo pip3 install scikit-learn
sudo pip3 install scikit-image
sudo pip3 install sklearn
sudo pip3 install keras


```
# These instructions are for python2 instead of python3. Have to do over. :-(

### RasperryPi 3 TensorFlow installation with Python3
https://github.com/samjabrahams/tensorflow-on-raspberry-pi

### Install TensorFlow via Jetson Hack Instructions

Another version of installing the Python version. It must be updated to python3 as well:
https://syed-ahmed.gitbooks.io/nvidia-jetson-tx2-recipes/content/first-question.html



http://www.jetsonhacks.com/2017/04/02/tensorflow-on-nvidia-jetson-tx2-development-kit/


General Dependencies
```bash
#!/bin/bash
# NVIDIA Jetson TX1
# Install TensorFlow dependencies
# Install Java
sudo add-apt-repository ppa:webupd8team/java
sudo apt-get update
sudo apt-get install oracle-java8-installer -y
# Install other dependencies
sudo apt-get install zip unzip autoconf automake libtool curl zlib1g-dev maven -y
sudo apt-get install python-numpy swig python-dev python-pip python-wheel -y
```
Bazel Dependencies
```bash
# NVIDIA Jetson TX1
# TensorFlow Installation
# Install Bazel
# We use the release distribution so that we don't have to build protobuf
#
INSTALL_DIR=$PWD
cd $HOME
wget --no-check-certificate https://github.com/bazelbuild/bazel/releases/download/0.4.5/bazel-0.4.5-dist.zip
unzip bazel-0.4.5-dist.zip -d bazel-0.4.5-dist
sudo chmod -R ug+rwx $HOME/bazel-0.4.5-dist
# git clone https://github.com/bazelbuild/bazel.git
cd bazel-0.4.5-dist
patch -p0 < $INSTALL_DIR/patches/bazel.patch
./compile.sh 
sudo cp output/bazel /usr/local/bin

```
notes:
```
matplotlib needs
sudo apt-get install libfreetype6-dev
sudo apt-get install python3-scipy
sudo apt-get install ipython3

time sudo pip3 install scikit-learn

real	7m8.795s
user	6m55.224s
sys	0m8.804s

```

## Decision System

Raspberry PI 3

Software configuration

```bash


```

###errors

```bash
fubar@tegra-ubuntu:~/Documents/tfinstall/installTensorFlowTX2$ time ./buildTensorFlow.sh 
WARNING: Sandboxed execution is not supported on your system and thus hermeticity of actions cannot be guaranteed. See http://bazel.build/docs/bazel-user-manual.html#sandboxing for more information. You can turn off this warning via --ignore_unsupported_sandboxing.
INFO: Found 1 target...
INFO: From Compiling tensorflow/core/common_runtime/gpu/gpu_tracer.cc:
tensorflow/core/common_runtime/gpu/gpu_tracer.cc:82:13: warning: 'const char* {anonymous}::getActivityOverheadKindString(CUpti_ActivityOverheadKind)' defined but not used [-Wunused-function]
 const char *getActivityOverheadKindString(CUpti_ActivityOverheadKind kind) {
             ^
INFO: From Compiling tensorflow/core/common_runtime/function.cc:
tensorflow/core/common_runtime/function.cc: In function 'bool tensorflow::ExpandInlineFunctions(tensorflow::FunctionLibraryRuntime*, tensorflow::Graph*)':
tensorflow/core/common_runtime/function.cc:931:34: warning: 'data.tensorflow::Endpoint::index' may be used uninitialized in this function [-Wmaybe-uninitialized]
     Node* n = AddIdentity(g, data);
                                  ^
tensorflow/core/common_runtime/function.cc:923:14: note: 'data.tensorflow::Endpoint::index' was declared here
     Endpoint data;  // Data input for the ret node.
              ^
tensorflow/core/common_runtime/function.cc:931:34: warning: 'data.tensorflow::Endpoint::node' may be used uninitialized in this function [-Wmaybe-uninitialized]
     Node* n = AddIdentity(g, data);
                                  ^
tensorflow/core/common_runtime/function.cc:923:14: note: 'data.tensorflow::Endpoint::node' was declared here
     Endpoint data;  // Data input for the ret node.
              ^
INFO: From Compiling tensorflow/core/distributed_runtime/master.cc:
tensorflow/core/distributed_runtime/master.cc: In member function 'tensorflow::Status tensorflow::DeviceFinder::Wait()':
tensorflow/core/distributed_runtime/master.cc:191:27: warning: comparison between signed and unsigned integer expressions [-Wsign-compare]
         for (int i = 0; i < targets_.size(); ++i) {
                           ^
INFO: From Compiling tensorflow/core/distributed_runtime/rpc/grpc_worker_service.cc:
In file included from ./tensorflow/stream_executor/trace_listener.h:22:0,
                 from ./tensorflow/stream_executor/platform.h:30,
                 from ./tensorflow/stream_executor/cuda/cuda_platform_id.h:19,
                 from ./tensorflow/core/platform/default/stream_executor.h:23,
                 from ./tensorflow/core/platform/stream_executor.h:24,
                 from ./tensorflow/core/common_runtime/gpu/gpu_util.h:23,
                 from tensorflow/core/distributed_runtime/rpc/grpc_worker_service.cc:27:
./tensorflow/stream_executor/kernel.h: In member function 'perftools::gputools::KernelArg perftools::gputools::KernelArgIterator::next()':
./tensorflow/stream_executor/kernel.h:307:28: warning: comparison between signed and unsigned integer expressions [-Wsign-compare]
                (arg_index_ == *shmem_indices_iter_)) {
                            ^
INFO: From Compiling tensorflow/core/distributed_runtime/rpc/grpc_worker_service_impl.cc:
tensorflow/core/distributed_runtime/rpc/grpc_worker_service_impl.cc: In function 'const char* tensorflow::GrpcWorkerMethodName(tensorflow::GrpcWorkerMethod)':
tensorflow/core/distributed_runtime/rpc/grpc_worker_service_impl.cc:50:1: warning: control reaches end of non-void function [-Wreturn-type]
 }
 ^
INFO: From Compiling tensorflow/python/client/tf_session_helper.cc:
tensorflow/python/client/tf_session_helper.cc: In function 'void tensorflow::TF_Run_wrapper_helper(TF_DeprecatedSession*, const char*, const TF_Buffer*, PyObject*, const NameVector&, const NameVector&, TF_Status*, tensorflow::PyObjectVector*, TF_Buffer*)':
tensorflow/python/client/tf_session_helper.cc:531:43: warning: 'py_array' may be used uninitialized in this function [-Wmaybe-uninitialized]
     py_outputs_safe.emplace_back(make_safe(py_array));
                                           ^
INFO: From Compiling tensorflow/core/distributed_runtime/master_session.cc:
tensorflow/core/distributed_runtime/master_session.cc: In member function 'tensorflow::Status tensorflow::MasterSession::ReffedClientGraph::RunPartitions(const tensorflow::MasterEnv*, tensorflow::int64, tensorflow::int64, tensorflow::SimpleGraphExecutionState*, tensorflow::MasterSession::PerStepState*, tensorflow::CallOptions*, const tensorflow::RunStepRequestWrapper&, tensorflow::MutableRunStepResponseWrapper*, tensorflow::CancellationManager*, bool)':
tensorflow/core/distributed_runtime/master_session.cc:569:25: warning: comparison between signed and unsigned integer expressions [-Wsign-compare]
       for (int i = 0; i < req.num_feeds(); ++i) {
                         ^
tensorflow/core/distributed_runtime/master_session.cc:581:39: warning: comparison between signed and unsigned integer expressions [-Wsign-compare]
         } else if (feeds_iter->second != i) {
                                       ^
tensorflow/core/distributed_runtime/master_session.cc:589:25: warning: comparison between signed and unsigned integer expressions [-Wsign-compare]
       for (int i = 0; i < req.num_fetches(); ++i) {
                         ^
tensorflow/core/distributed_runtime/master_session.cc: At global scope:
tensorflow/core/distributed_runtime/master_session.cc:444:13: warning: 'bool tensorflow::CopyIfNeeded(tensorflow::TensorProto*, tensorflow::TensorProto*)' defined but not used [-Wunused-function]
 static bool CopyIfNeeded(TensorProto* in, TensorProto* out) {
             ^
INFO: From Compiling tensorflow/core/debug/debug_io_utils.cc:
tensorflow/core/debug/debug_io_utils.cc:212:15: warning: 'tensorflow::Status tensorflow::CloseDebugURL(const string&)' defined but not used [-Wunused-function]
 static Status CloseDebugURL(const string& debug_url) { return Status::OK(); }
               ^
INFO: From Compiling tensorflow/core/kernels/tensor_array_ops.cc:
tensorflow/core/kernels/tensor_array_ops.cc: In member function 'virtual tensorflow::Status tensorflow::TensorArrayGradOp::CreateTensorArray(tensorflow::OpKernelContext*, tensorflow::ResourceMgr*, tensorflow::Tensor*, tensorflow::TensorArray**)':
tensorflow/core/kernels/tensor_array_ops.cc:312:5: warning: 'marked_size' may be used uninitialized in this function [-Wmaybe-uninitialized]
     };
     ^
INFO: From Compiling tensorflow/python/pywrap_tensorflow.cc:
bazel-out/local_linux-opt/bin/tensorflow/python/pywrap_tensorflow.cc: In function 'PyObject* _wrap_PyRecordReader_New(PyObject*, PyObject*)':
bazel-out/local_linux-opt/bin/tensorflow/python/pywrap_tensorflow.cc:4764:138: warning: 'arg2' may be used uninitialized in this function [-Wmaybe-uninitialized]
     result = (tensorflow::io::PyRecordReader *)tensorflow::io::PyRecordReader::New((string const &)*arg1,arg2,(string const &)*arg3,arg4);
                                                                                                                                          ^
At global scope:
cc1plus: warning: unrecognized command line option '-Wno-self-assign'
Target //tensorflow/tools/pip_package:build_pip_package up-to-date:
  bazel-bin/tensorflow/tools/pip_package/build_pip_package
INFO: Elapsed time: 4187.077s, Critical Path: 3994.60s

real	69m47.322s
user	0m0.220s
sys	0m0.400s

```
