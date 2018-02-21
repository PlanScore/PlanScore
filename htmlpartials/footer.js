const htmlblock = `
    <div class="container-fluid footer">
    <div class="row">
        <p class="col-md-2">
            <a target="_blank" href="mailto:info@planscore.org"><img src="https://planscore.org/images/email-logo.svg"> info@planscore.org</a>
        </p>
        <p class="col-md-2">
            <a target="_blank" href="https://twitter.com/PlanScore"><img src="https://planscore.org/images/twitter-logo.svg"> @PlanScore</a>
        </p>
        <p class="col-md-2">
            <a target="_blank" href="https://github.com/PlanScore/PlanScore"><img src="https://planscore.org/images/github-logo.svg"> Github</a>
        </p>
    </div>
    <div class="row">
    <span class="col-md-12">PlanScore is a fiscally sponsored project of <a href="http://www.greeninfo.org/" target="_blank"><img src="https://planscore.org/images/greeninfo.svg"> GreenInfo Network</a></span>
    </div>
    </div>

    <script async src="https://www.googletagmanager.com/gtag/js?id=UA-65629552-4"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());

      gtag('config', 'UA-65629552-4');
    </script>
    `;
module.exports = htmlblock;
