function createLimkoBotForm() {
  var SUPERVISOR = 'Supervisor name and email';

  var form = FormApp.create('What would you ask a university chatbot?');
  form.setDescription(
    'We are final year Software Engineering students at Limkokwing University building a WhatsApp ' +
    'chatbot that answers student questions about fees, exams, registration and university policy. ' +
    'This questionnaire takes about three minutes. Taking part is voluntary, and you can stop at any ' +
    'point without penalty. We do not ask for your name, phone number or email. Your answers will be ' +
    'used only for our dissertation and stored securely until 30 days after final submission. ' +
    'Supervisor: ' + SUPERVISOR + '.');
  form.setCollectEmail(false);
  form.setLimitOneResponsePerUser(false);
  form.setAllowResponseEdits(false);
  form.setProgressBar(true);
  form.setConfirmationMessage('Thank you. If you have a concern about this study, contact ' + SUPERVISOR + '.');

  var topics = ['Fees', 'Exams', 'Registration', 'Policy', 'Other'];

  var consent = form.addCheckboxItem();
  consent.setTitle('Consent')
    .setHelpText('I have read the information above and agree to take part.')
    .setChoices([consent.createChoice('I agree')])
    .setRequired(true);

  form.addPageBreakItem().setTitle('About you (optional)');
  form.addMultipleChoiceItem()
    .setTitle('Which year are you in?')
    .setChoiceValues(['Foundation', 'Year 1', 'Year 2', 'Year 3', 'Year 4', 'Postgraduate'])
    .setRequired(false);
  form.addTextItem()
    .setTitle('Which faculty or programme are you in?')
    .setRequired(false);

  form.addPageBreakItem().setTitle('How you find information now');
  form.addCheckboxItem()
    .setTitle('Where do you usually look for information about fees, exams or registration?')
    .setHelpText('Tick all that apply.')
    .setChoiceValues(['Notice boards', 'Front desk or office visit', 'Staff email',
                      'Student WhatsApp groups', 'Lecturers', 'Friends'])
    .showOtherOption(true)
    .setRequired(false);
  form.addCheckboxItem()
    .setTitle('Which kinds of information are hardest to get?')
    .setHelpText('Tick all that apply.')
    .setChoiceValues(['Fees and payments', 'Exam timetables', 'Registration deadlines',
                      'Programme or course details', 'Academic policies', 'Transcripts and documents'])
    .showOtherOption(true)
    .setRequired(false);
  form.addMultipleChoiceItem()
    .setTitle('How long does it usually take to get an answer to a simple question?')
    .setChoiceValues(['Under an hour', 'Same day', '2 to 3 days', 'More than 3 days',
                      'I often never get an answer'])
    .setRequired(false);

  form.addPageBreakItem()
    .setTitle('Your questions')
    .setHelpText(
      'Imagine you could message a university chatbot on WhatsApp at any time. What would you ask? ' +
      'Write real questions you have asked or would ask. Please do not include your name, ' +
      'student number or phone number.'
    );

  for (var i = 1; i <= 3; i++) {
    form.addParagraphTextItem()
      .setTitle('Question ' + i)
      .setHelpText(i === 1
        ? 'Required. Write it exactly as you would type it.'
        : 'Optional. If you add a question, please also choose its topic below.')
      .setRequired(i === 1);
    form.addListItem()
      .setTitle('Topic for question ' + i)
      .setChoiceValues(topics)
      .setRequired(i === 1);
  }

  form.addPageBreakItem().setTitle('Anything else (optional)');
  form.addParagraphTextItem()
    .setTitle('Is there anything else you would want the chatbot to do?')
    .setRequired(false);

  var sheet = SpreadsheetApp.create('LimkoBot Query Collection Responses');
  form.setDestination(FormApp.DestinationType.SPREADSHEET, sheet.getId());

  Logger.log('Edit the form: ' + form.getEditUrl());
  Logger.log('Share with students: ' + form.getPublishedUrl());
  Logger.log('Responses spreadsheet: ' + sheet.getUrl());
}
