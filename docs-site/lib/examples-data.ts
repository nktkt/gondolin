export type ExampleCategory =
  | "quickstart"
  | "vision"
  | "sequence"
  | "generative"
  | "rl"
  | "operator-learning"
  | "verification"
  | "interop";

export interface Example {
  slug: string;
  title: string;
  blurb: string;
  command: string;
  category: ExampleCategory;
  tags: string[];
}

export const examples: Example[] = [
  // ---------------------- Quickstart ----------------------
  {
    slug: "quickstart_tensors",
    title: "Tensor Basics",
    blurb:
      "Introductory walkthrough of Gondolin tensors, shapes, and elementary ops.",
    command: "lake exe gondolin quickstart_tensors",
    category: "quickstart",
    tags: ["cpu", "intro"],
  },
  {
    slug: "quickstart_autograd",
    title: "Autograd Basics",
    blurb:
      "Build a small computation graph and inspect reverse-mode gradients end to end.",
    command: "lake exe gondolin quickstart_autograd --dtype float --backend eager",
    category: "quickstart",
    tags: ["cpu", "autograd", "eager"],
  },
  {
    slug: "quickstart_mlp",
    title: "Simple MLP Train",
    blurb:
      "Train a tiny multilayer perceptron in a few steps to see the optimizer loop.",
    command:
      "lake exe gondolin quickstart_mlp --steps 20 --dtype float --backend eager",
    category: "quickstart",
    tags: ["cpu", "training", "eager"],
  },

  // ---------------------- Supervised / Vision ----------------------
  {
    slug: "mlp",
    title: "MLP Regression",
    blurb:
      "Auto-MPG tabular regression with a dense MLP and minibatch training loop.",
    command:
      "lake exe -K cuda=true gondolin mlp --cuda --epochs 100 --lr 0.003 --log data/model_zoo/mlp_trainlog.json",
    category: "vision",
    tags: ["cuda", "tabular", "supervised"],
  },
  {
    slug: "cnn",
    title: "CNN on CIFAR-10",
    blurb:
      "Compact convolutional classifier trained with fast CUDA kernels on CIFAR-10.",
    command:
      "lake exe -K cuda=true gondolin cnn --cuda --fast-kernels --n-total 2000 --epochs 25 --lr 0.001",
    category: "vision",
    tags: ["cuda", "fast-kernels", "cifar10"],
  },
  {
    slug: "resnet",
    title: "ResNet Classifier",
    blurb:
      "Residual network on CIFAR-10 using fused CUDA kernels for the conv path.",
    command:
      "lake exe -K cuda=true gondolin resnet --cuda --fast-kernels --n-total 2000 --epochs 15 --lr 0.001",
    category: "vision",
    tags: ["cuda", "fast-kernels", "residual"],
  },
  {
    slug: "vit",
    title: "Vision Transformer",
    blurb:
      "Small ViT patch encoder for image classification with attention blocks.",
    command:
      "lake exe -K cuda=true gondolin vit --cuda --fast-kernels --n-total 2000 --epochs 10 --lr 0.001",
    category: "vision",
    tags: ["cuda", "attention", "patches"],
  },
  {
    slug: "lstm_regression",
    title: "LSTM Forecasting",
    blurb:
      "Forecast household power windows with an LSTM and printed before/after rows.",
    command:
      "lake exe -K cuda=true gondolin lstm_regression --cuda --steps 200 --windows 96",
    category: "sequence",
    tags: ["cuda", "forecasting", "windows"],
  },

  // ---------------------- Sequence ----------------------
  {
    slug: "rnn",
    title: "Vanilla RNN",
    blurb: "Reference recurrent cell for short character-level sequence tasks.",
    command: "lake exe gondolin rnn --steps 100",
    category: "sequence",
    tags: ["cpu", "recurrent"],
  },
  {
    slug: "lstm",
    title: "LSTM Cell",
    blurb: "Stacked LSTM check exercising gated state on a tiny corpus.",
    command: "lake exe gondolin lstm --steps 100",
    category: "sequence",
    tags: ["cpu", "recurrent", "gated"],
  },
  {
    slug: "transformer",
    title: "Transformer Block",
    blurb:
      "Encoder-style Transformer building blocks with multi-head attention.",
    command: "lake exe -K cuda=true gondolin transformer --cuda --steps 100",
    category: "sequence",
    tags: ["cuda", "attention"],
  },
  {
    slug: "gpt2",
    title: "GPT-style Causal LM",
    blurb:
      "Compact GPT-style decoder trained on tiny-shakespeare with sampling controls.",
    command:
      'lake exe -K cuda=true gondolin gpt2 --cuda --fast-kernels --tiny-shakespeare --steps 300 --windows 32 --lr 0.001 --prompt "ROMEO:" --generate 220',
    category: "sequence",
    tags: ["cuda", "fast-kernels", "causal-lm"],
  },
  {
    slug: "mamba",
    title: "Mamba State-Space LM",
    blurb:
      "Selective state-space sequence model trained on tiny-shakespeare windows.",
    command:
      'lake exe -K cuda=true gondolin mamba --cuda --fast-kernels --tiny-shakespeare --steps 2000 --windows 384 --lr 0.004 --prompt "ROMEO:" --generate 260',
    category: "sequence",
    tags: ["cuda", "fast-kernels", "ssm"],
  },
  {
    slug: "gpt_adder",
    title: "GPT Adder",
    blurb:
      "Train a tiny GPT to add two digits and verify a specific input pair.",
    command: "lake exe gondolin gpt_adder --steps 1000 --a 7 --b 8",
    category: "sequence",
    tags: ["cpu", "synthetic"],
  },

  // ---------------------- Generative ----------------------
  {
    slug: "vae",
    title: "Variational Autoencoder",
    blurb:
      "Train a small VAE with the standard ELBO objective and write a TrainLog.",
    command:
      "lake exe -K cuda=true gondolin vae --cuda --steps 25 --log data/model_zoo/vae_trainlog.json",
    category: "generative",
    tags: ["cuda", "elbo", "latent"],
  },
  {
    slug: "gan",
    title: "GAN Training",
    blurb:
      "Lightweight generator/discriminator pair with an adversarial loop.",
    command:
      "lake exe -K cuda=true gondolin gan --cuda --steps 25 --log data/model_zoo/gan_trainlog.json",
    category: "generative",
    tags: ["cuda", "adversarial"],
  },
  {
    slug: "diffusion",
    title: "Diffusion Model",
    blurb:
      "Tiny denoising diffusion model on CIFAR-10 with PPM sample output.",
    command:
      "lake exe -K cuda=true gondolin diffusion --cuda --fast-kernels --dataset cifar10 --n-total 800 --steps 200 --T 100",
    category: "generative",
    tags: ["cuda", "fast-kernels", "denoising"],
  },
  {
    slug: "mae",
    title: "Masked Autoencoder",
    blurb:
      "Patch-masking pretraining objective with reconstructive decoder head.",
    command:
      "lake exe -K cuda=true gondolin mae --cuda --steps 25 --log data/model_zoo/mae_trainlog.json",
    category: "generative",
    tags: ["cuda", "self-supervised"],
  },

  // ---------------------- Operator Learning ----------------------
  {
    slug: "fno1d_burgers",
    title: "FNO on 1D Burgers",
    blurb:
      "Fourier neural operator trained on the 1D Burgers equation dataset.",
    command:
      "lake exe -K cuda=true gondolin fno1d_burgers --cuda --steps 200 --log data/model_zoo/fno1d_burgers_trainlog.json",
    category: "operator-learning",
    tags: ["cuda", "pde", "spectral"],
  },

  // ---------------------- Reinforcement Learning ----------------------
  {
    slug: "ppo_cartpole",
    title: "PPO on CartPole",
    blurb:
      "Proximal Policy Optimization agent solving the CartPole control task.",
    command: "lake exe gondolin ppo_cartpole --updates 200",
    category: "rl",
    tags: ["cpu", "policy-gradient", "control"],
  },
  {
    slug: "ppo_gridworld",
    title: "PPO on GridWorld",
    blurb:
      "PPO agent navigating a discrete GridWorld environment for many updates.",
    command: "lake exe gondolin ppo_gridworld --updates 200",
    category: "rl",
    tags: ["cpu", "policy-gradient", "discrete"],
  },
  {
    slug: "dqn_replay",
    title: "DQN with Replay",
    blurb:
      "Deep Q-Network training with a replay buffer and target network sync.",
    command: "lake exe gondolin dqn_replay --updates 200",
    category: "rl",
    tags: ["cpu", "value-based", "replay"],
  },

  // ---------------------- Interop / Data ----------------------
  {
    slug: "pytorch_roundtrip",
    title: "PyTorch Roundtrip",
    blurb:
      "Export a Gondolin model to PyTorch and re-import the saved weights.",
    command: "lake exe gondolin pytorch_roundtrip --model mlp --action import",
    category: "interop",
    tags: ["pytorch", "export", "import"],
  },
  {
    slug: "torch_ir_pytorch",
    title: "Torch IR to PyTorch",
    blurb:
      "Lower the Gondolin Torch IR to a runnable PyTorch module printed to stdout.",
    command: "lake exe gondolin torch_ir_pytorch --arch mlp",
    category: "interop",
    tags: ["pytorch", "ir", "lowering"],
  },
  {
    slug: "data_csv",
    title: "CSV Data Loader",
    blurb:
      "Stream CSV records into typed minibatches under the shared loader path.",
    command: "lake exe gondolin data_csv --epochs 1 --batch 5 --dtype float --backend eager",
    category: "interop",
    tags: ["data", "csv", "loader"],
  },

  // ---------------------- Verification ----------------------
  {
    slug: "gondolin-robustness",
    title: "Gondolin Robustness",
    blurb:
      "Build a compact classifier and check its margin with IBP, forward CROWN, and backward CROWN.",
    command: "lake exe verify -- gondolin-robustness",
    category: "verification",
    tags: ["ibp", "crown", "robustness"],
  },
  {
    slug: "gondolin-crown-ops",
    title: "CROWN Nonlinear Ops",
    blurb:
      "Exercise softmax and MSE-loss bound propagation on compact Gondolin graphs.",
    command: "lake exe verify -- gondolin-crown-ops",
    category: "verification",
    tags: ["crown", "softmax", "nonlinear"],
  },
  {
    slug: "digits",
    title: "Digits Certified Accuracy",
    blurb:
      "Load bundled sklearn digits weights and report IBP/CROWN certified accuracy.",
    command: "lake exe verify -- digits --eps=0.02 --max=360",
    category: "verification",
    tags: ["ibp", "crown", "certified-accuracy"],
  },
  {
    slug: "margin-cert",
    title: "Margin Certificate Check",
    blurb:
      "Recompute the exported digits logit-margin predicate from JSON bounds.",
    command: "lake exe verify -- margin-cert",
    category: "verification",
    tags: ["certificate", "json"],
  },
  {
    slug: "spline-cert",
    title: "Piecewise Polynomial Cert",
    blurb:
      "Check an exact rational piecewise polynomial certificate inside Lean.",
    command: "lake exe verify -- spline-cert",
    category: "verification",
    tags: ["certificate", "exact", "splines"],
  },
];
