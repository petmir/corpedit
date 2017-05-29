###########################################################
###  data for testing segmentio.rebase_changelog        ###
###  (easy data, not requiring an advanced algorithm)   ###
###########################################################

The same data and operations as in model_test.test_do_some_edits_parallel_workflow().


definition of w1edit1
======================

-----------------------------------------------------------------------------------
Rožnov	Rožnov	k1gInSc1	Rožnov
si	se	k3c3xPyFqP	
premiéru	premiér	k1gMnSc3qP	premiér
nového	nový	k2eAgNnSc2d1qP	nové
hřiště	hřiště	k1gNnSc2qP	hřiště
-----------------------------------------------------------------------------------

     |
     v

-----------------------------------------------------------------------------------
Rožnov	Rožnov	k1gInSc1	Rožnov
si	se	k3c3xPyFqP	[NOTE: DELETED THE NEXT LINE (THE LEMMA THERE LOOKED WRONG)]
nového	nový	k2eAgNnSc2d1qP	nové
hřiště	hřiště	k1gNnSc2qP	hřiště
-----------------------------------------------------------------------------------


definition of w1edit2
======================

-----------------------------------------------------------------------------------
Rožnov	Rožnov	k1gInSc1	Rožnov
si	se	k3c3xPyFqP	[NOTE: DELETED THE NEXT LINE (THE LEMMA THERE LOOKED WRONG)]
nového	nový	k2eAgNnSc2d1qP	nové
hřiště	hřiště	k1gNnSc2qP	hřiště
nenechal	nechat	k5eNaPmAgInSrDaPqP	
-----------------------------------------------------------------------------------

     |
     v

-----------------------------------------------------------------------------------
Rožnov	Rožnov	k1gInSc1	Rožnov
si	se	k3c3xPyFqP	[NOTE: DELETED THE NEXT LINE (THE LEMMA THERE LOOKED WRONG)]
ADDED LINE 1
ADDED LINE 2
nového	nový	k2eAgNnSc2d1qP	nové
hřiště	hřiště	k1gNnSc2qP	hřiště
nenechal	nechat	k5eNaPmAgInSrDaPqP	
-----------------------------------------------------------------------------------


definition of w2edit3
======================

-----------------------------------------------------------------------------------
Sestupný	sestupný	k2eAgInSc1d1qP	sestupný
kurs	kurs	k1gInSc1	kurs
po	po	k7c6qP	
víkendu	víkend	k1gInSc6qP	víkend
určitě	určitě	k6eAd1	
nabere	nabrat	k5eAaPmIp3nSaPrDqP	
Spytihněv	Spytihněv	k1gFnSc1qG	Spytihněv
<g/>
-----------------------------------------------------------------------------------

     |
     v

-----------------------------------------------------------------------------------
Sestupný	sestupný	k2eAgInSc1d1qP	sestupný
kurs	kurs	k1gInSc1	kurs
(DELETED THESE 4 WORDS)
SpytihněVVVVV	Spytihněv	k1gFnSc1qG	Spytihněv
<g/>
-----------------------------------------------------------------------------------


definition of w1edit4
======================

-----------------------------------------------------------------------------------
Rožnov	Rožnov	k1gInSc1	Rožnov
si	se	k3c3xPyFqP	[NOTE: DELETED THE NEXT LINE (THE LEMMA THERE LOOKED WRONG)]
nového	nový	k2eAgNnSc2d1qP	nové
-----------------------------------------------------------------------------------

     |
     v

-----------------------------------------------------------------------------------
Rožnov	Rožnov	k1gInSc1	Rožnov
si	se	k3c3xPyFqP 
premiéru	premiéra	<SOMEONE PLZ PUT CORRECT CODE HERE>	premiéra  #fixed the lemma
nového	nový	k2eAgNnSc2d1qP	nové
-----------------------------------------------------------------------------------


scenario
========

Steps: 

1. open a window (w1), do w1edit1 in it
2. do w1edit2 in w1
3. open another window (w2), do w2edit3 in it
4. commit changes in w2 (that is: w2edit3)
5. commit changes in w1 (that is: w1edit1, w1edit2)
6. do edit4 in w1

After each step, check that the content of each window is correct. 


file naming convention
======================
TODO (later); this is outdated:
#How the files are named (example): 
#
#    step2c-cztenten_994-rev0-w1edit1-APPLY-w1edit2.patch
#        =  changelog that does step 2 
#            (that is: apply edit w1edit1 on file <cztenten_994:revision 0, after applying w1edit1>)
#
#    step2r-cztenten_994-rev0-w1edit1-w1edit2.vert
#        =  result of step 2 
#            (that is: file <cztenten_994:revision 0, after applying w1edit1 and w1edit2>
#
#    step3cNEEDREBASE-cztenten_994-rev0-APPLY-w2edit3.patch
#        =  changelog that does step 3 
#            (that is: apply edit w2edit3 on file <cztenten_994:revision 0>)


note on how the editor should work
==================================

----------------------------------------------------------------------------------
NOTE: The stuff about the minimum distance no longer applies, as I implemented the 
      more ambitious algorithm (see segmentio_testdata/rebasing/README.txt).
      The algorithm I made doesn't mind if the lines are right next to each other.

      *** And the window is ALWAYS rebased after any reload. ***
        ( ->  not doing that would actually cause this problem: 
              the line numbers would be from the head revision so any change would 
              have bad line numbers in the window changelog)
----------------------------------------------------------------------------------

    (((OUTDATED: 
    When reloading the window (after edit, or just after moving to another line or 
    just reloading at the same line), NEVER rebase the window. The base revision of 
    the window stays the same. 

        -> reason: Otherwise the window's revision could possibly change any time. 
                   It's better to have it this way, where the window's revision 
                   (and thus also the window changelog) is changed only when commiting. 
                   That's something the user can actively do and plan for, not just 
                   something that can come at any moment by surprise.
                   Also, an event such as just a read can easily happen by accident unnoticed, 
                   which could lead to frustrating debugging. Compared to that, commits are 
                   easy to keep track of.
                    
                   NOTE: But even for reading, the changelog must be rebased on-the-fly. If 
                   it fails because someone commited changes closer than the minimum distance, 
                   the user of the window will get an error (a conflict), even just reading.


    After commit, ALWAYS rebase. 

        -> reason: Otherwise, if the user kept editing after he commited the
                   window, he would need to keep the minimum distance not just from edits of
                   other users, but also his own edits in the same window before the commit.
                   That would be weird and annoying. 
    )))

